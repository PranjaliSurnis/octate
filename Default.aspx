<%@ Page Title="COVIID-19" Language="C#" MasterPageFile="~/Site.Master" AutoEventWireup="true" CodeFile="Default.aspx.cs" Inherits="_Default" %>

<asp:Content ID="BodyContent" ContentPlaceHolderID="MainContent" runat="server">

    <div class="jumbotron" style="height:400px;padding:3%;margin:3%">
        <h1>COVID-19</h1>
        <hr  runat="server" />
        <p class="lead">Write your Privacy Policy in plain, easy-to-understand language. Update your policy regularly to reflect changes in the law, in your business, or within your protocols. Notify users of these updates, and include the effective date with your policy. Be transparent and remain true to your commitment to user privacy.</p>
         <asp:CheckBox runat="server" ID="accept" Text="&nbsp&nbsp;I Accept terms & conditions."/> 
        <div>
        <asp:Button runat="server"  id="submit" class="btn btn-primary btn-lg" style="margin-top:1%;" Text="Submit" ValidationGroup="sub" OnClick="submit_Click"  />
    </div>
    </div>

    
</asp:Content>
