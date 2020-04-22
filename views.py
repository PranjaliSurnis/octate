from django.shortcuts import render
from .models import Investigator
from .models import Publication
from .models import Grant
from .models import ClinicalTrial
from .models import terms_list
from .models import items_list
from .models import similarity_matrix
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.views.generic import ListView
from sklearn.metrics.pairwise import cosine_similarity, linear_kernel
from django.db.models import FloatField, Subquery, Q, FloatField, Aggregate, F, Value, Case, When
from django.db.models.functions import Cast
from django.views.generic import TemplateView
from .charts import MeshChart, AuthorChart, PublicationHistoryChart
from django.http import Http404
import pygal
#TODO: Clean imports

def index(request):
	return render(request, 'searchFunction/index.html',{})

#TODO: some tables are queried twice, can be simplified to increase performance
#This function controls the keyword search functionality of the site and outputs to the results.html file
def results(request):
	if request.method == 'GET':
		search_query = request.GET.get('search_box', None) #Get user query term from the search box
		#This looks complicated, but essentially this line just tacks on a new variable called 'rank' that is calculated dynamically via the searchRank function, then filters out anything below .01 and places them in desc order.
		Grants = Grant.objects.annotate(rank=SearchRank(SearchVector('title', weight='A')+SearchVector('grantText', weight='B'), search_query)).filter(rank__gte=0.01).order_by('-rank') 
		#Publications dont appear directly in search results, but they are used to check for references in an authors publication history. So if a user searches for 'cancer', it will pull up authors who have the word 'cancer' in their publications.
		publications = Publication.objects.filter(title__icontains=search_query) | Publication.objects.filter(abstract__icontains=search_query)
		profiles = Investigator.objects.filter(fullName__icontains=search_query).annotate(rank=SearchRank(SearchVector('fullName', weight='A'), search_query)) | Investigator.objects.filter(investigator_tag__in=publications.values('investigator_tag'))
		# profiles = profiles.filter(rank__gte=0.01).order_by('-rank').values_list()
		#Clinical trials are handled exactly the same as grants above.
		ClinicalTrials = ClinicalTrial.objects.filter(title__icontains=search_query).annotate(rank=SearchRank(SearchVector('title', weight='A') + SearchVector('conditions', weight='B'), search_query)).filter(rank__gte=0.01).order_by('-rank')
		querySize = ClinicalTrials.count() + profiles.count() + Grants.count()

		return render(request, 'searchFunction/results.html',{'Grants' : Grants, 'profiles' : profiles, 'ClinicalTrials' : ClinicalTrials, 'query': search_query, 'size' : querySize}) 


#Here we have the term matched to its vector, then take the vectors and iterate through all author/grant vectors and find the cos value for each combination dynamically. This is among the most computationally expensive parts of the program.
def LSI(request):
	if request.method == 'GET':
		t=[]
		LSI_search_query = request.GET.get('search_box', None)
		preterm = LSI_search_query.split(' ') #split multiword terms
		for a in preterm:
			t.append(a.lower()) #makes everything lowercase
		termVectorQS = terms_list.objects.filter(term__in=t)#match searched terms to vectors
		termVectors = [[sum(x) for x in zip(*termVectorQS.values_list('termVector', flat=True))]] #This line adds vector values together if there are multiple matches
		items = items_list.objects.all()
		cosDict = {}
		if termVectorQS: 
			#creates a list of all cosine scores between the term vector and all item vectors
			cos = list(cosine_similarity(termVectors,items.values_list('itemVector', flat=True))[0])

			#maps all cosine scores to their respective indexKeys
			for x in cos:
				cosDict[cos.index(x)+1] = x

			#copy any cos values over .1 to a copy of the dict, effectively removing very low similarity scores
		cosDict = { k : "{:.2f}".format(v) for k,v in cosDict.items() if v>.1}
		dictSize = len(cosDict)
		#indexKey lookups to fetch matching items
		profiles = Investigator.objects.filter(indexKey__in=cosDict.keys())
		Grants = Grant.objects.filter(indexKey__in=cosDict.keys())
		ClinicalTrials = ClinicalTrial.objects.filter(indexKey__in=cosDict.keys())
		return render(request, 'searchFunction/LSI.html',{'Grants' : Grants, 'profiles': profiles, 'ClinicalTrials' : ClinicalTrials, 'cosDict' : cosDict, 'query': LSI_search_query, 'size' : dictSize})

#Browse functionality, outputs to browse.html
def browse(request):
	if request.method == 'GET':
		Grants = Grant.objects.all()
		ClinicalTrials = ClinicalTrial.objects.all()
		profiles = Investigator.objects.all()
		querySize = ClinicalTrials.count() + profiles.count() + Grants.count()

		return render(request, 'searchFunction/browse.html',{'Grants' : Grants, 'profiles': profiles, 'ClinicalTrials' : ClinicalTrials, 'size' : querySize})

#This controls user profiles. Look in charts.py if you need to change how the charts work. 
def userprofile(request): 
	if request.method == 'GET':
		p=(request.GET.get('investigator_tag'))
		investigator = Investigator.objects.all()
		profiles = investigator.filter(investigator_tag__exact=p)
		publications = Publication.objects.filter(investigator_tag__exact=p)
		items = items_list.objects.all()
		termVectorQS = items.filter(indexKey__in = profiles.values('indexKey'))#match searched terms to vectors
		termVectors = [[sum(x) for x in zip(*termVectorQS.values_list('itemVector', flat=True))]] #This line adds vector values together if there are multiple matches
		
		cosDict = {}

		#creates a list of all cosine scores between the term vector and all item vectors
		cos = list(cosine_similarity(termVectors,items.values_list('itemVector', flat=True))[0])

		#maps all cosine scores to their respective indexKeys
		for x in cos:
			cosDict[cos.index(x)+1] = x

		#copy any cos values over .1 to a copy of the dict, effectively removing very low similarity scores
		cosDict = { k : "{:.2f}".format(v) for k,v in cosDict.items() if v>.1 and v<1.0}
		dictSize = len(cosDict)
		#indexKey lookups to fetch matching items
		profileList = Investigator.objects.filter(indexKey__in=cosDict.keys())
		Grants = Grant.objects.filter(indexKey__in=cosDict.keys())
		ClinicalTrials = ClinicalTrial.objects.filter(indexKey__in=cosDict.keys())

		#This bit of code is a framework for future plans. Eventually I'd like create a foreignkey relationship in the db so that items can reference their associated cosine scores with select_related(). Will be much faster and more scalable, but difficult (impossible?) to do with how tables are currently set up.

		# simAll = similarity_matrix.objects.filter(y_axis__in=profiles).filter(cosine_score__gt=0)
		# simKeys = simAll.values('x_axis')
		# simGrants = Grant.objects.filter(indexKey__in=simKeys)
		# simAuthors = investigator.filter(indexKey__in=simKeys)
		# simClinicalTrials = ClinicalTrial.objects.filter(indexKey__in=simKeys)


		MeshChart.chart(publications)
		AuthorChart.chart(publications)
		PublicationHistoryChart.chart(publications)

		return render(request, 'searchFunction/userprofile.html', {'profiles' : profiles, 'Grants' : Grants, 'profileList': profileList, 'ClinicalTrials' : ClinicalTrials, 'publications': publications, 'cosDict' : cosDict} )

