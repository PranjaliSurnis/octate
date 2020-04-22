using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;
using System.Security.Cryptography;
using System.Text;
using System.Configuration;
using System.Data.SqlClient;
using System.Data;

public partial class _Default : Page
{
    string connstring = ConfigurationManager.ConnectionStrings["itmall"].ConnectionString;
    string deviceId, cipher;
    protected void Page_Load(object sender, EventArgs e)
    {

#pragma warning disable CS0618 // Type or member is obsolete
        deviceId = Dns.GetHostByName(Environment.MachineName).AddressList[0].ToString();
#pragma warning restore CS0618 // Type or member is obsolete
        cipher = Encrypt(deviceId, "sblw-3hn8-sqoy19");
        SqlDataAdapter adapter;
        DataSet ds = new DataSet();
        SqlConnection con = new SqlConnection(connstring);
        SqlCommand cmd = new SqlCommand("SelectDevice", con);
        cmd.CommandType = CommandType.StoredProcedure;
        cmd.Parameters.AddWithValue("deviceid", cipher);
        con.Open();
        adapter = new SqlDataAdapter(cmd);
        adapter.Fill(ds);
        con.Close();
        if(ds.Tables.Count!=0)
        { 
            Response.Redirect("~/RecordAudio.aspx?page=" + cipher);
        }
          


    }

    protected void submit_Click(object sender, EventArgs e)
    {
        if (accept.Checked == true)
        {

            Response.Redirect("~/PersonalInfo.aspx?page=" + cipher);
        }
        else
        {
            ScriptManager.RegisterClientScriptBlock(Page, typeof(Page), "ClientScript", "alert('Please accept terms & conditions.')", true);

        }

    }

    public static string Encrypt(string input, string key)
    {
        byte[] inputArray = UTF8Encoding.UTF8.GetBytes(input);
        TripleDESCryptoServiceProvider tripleDES = new TripleDESCryptoServiceProvider();
        tripleDES.Key = UTF8Encoding.UTF8.GetBytes(key);
        tripleDES.Mode = CipherMode.ECB;
        tripleDES.Padding = PaddingMode.PKCS7;
        ICryptoTransform cTransform = tripleDES.CreateEncryptor();
        byte[] resultArray = cTransform.TransformFinalBlock(inputArray, 0, inputArray.Length);
        tripleDES.Clear();
        return Convert.ToBase64String(resultArray, 0, resultArray.Length);
    }


    public static string Decrypt(string input, string key)
    {
        byte[] inputArray = Convert.FromBase64String(input);
        TripleDESCryptoServiceProvider tripleDES = new TripleDESCryptoServiceProvider();
        tripleDES.Key = UTF8Encoding.UTF8.GetBytes(key);
        tripleDES.Mode = CipherMode.ECB;
        tripleDES.Padding = PaddingMode.PKCS7;
        ICryptoTransform cTransform = tripleDES.CreateDecryptor();
        byte[] resultArray = cTransform.TransformFinalBlock(inputArray, 0, inputArray.Length);
        tripleDES.Clear();
        return UTF8Encoding.UTF8.GetString(resultArray);
    }
}