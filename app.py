
from fileinput import close, filename
from operator import eq
from urllib import response
import dotenv
import flask
from flask import request, jsonify, render_template, send_file, send_from_directory, url_for, redirect, flash, session, make_response
from flask_session import Session
import pymongo
import bcrypt
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import random
import encryption.encrypt as encrypt1
import logging
import os, glob
from dotenv import dotenv_values, load_dotenv
import time
import csv
import io
import pdfkit

logging.basicConfig(filename='record.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
 
app = flask.Flask(__name__)
app._static_folder = 'static'
app.config["DEBUG"] = True
app.secret_key = "super secret key"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

load_dotenv()

DB_URL = os.getenv("DB_URL")

DB_NAME = os.getenv("DB_NAME")

db_con = pymongo.MongoClient(DB_URL)

db_name = db_con[DB_NAME]

db_userlogin = db_name['userlogin']

db_userdata = db_name['userdata']

db_transactions = db_name['transaction']

db_carddetails = db_name['carddetails']

db_beneficiarydetails = db_name['beneficiarydetails']

print("---------------------------------------------------------------------")

user_found = []

@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404

@app.route('/',methods=["POST", "GET"])
def index():
    
    if session.get('username') is not None:
        #print("session name is true: ", session.get('username'))
        return redirect(url_for('home'))
    else:
        #print("In Main Route session name is false: ", session.get('username'))
        return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template("register.html")

@app.route('/test', methods=['GET', 'POST'])
def home_new():
    return render_template("test.html")
 

@app.route('/user_register', methods=('GET','POST'))
def user_register():
    if request.method=='POST':
        username_in = request.form['username']
        password_in1 = request.form['password1']
        password_in2 = request.form['password2']
        name_in = request.form['fullname']
        email_in = request.form['email']
        username_ln = len(username_in)
        name_ln = len(name_in)
        card_second_last = str(random.randint(1001, 9999))
        card_last = str(random.randint(1001, 9999))
        card_cvv = str(random.randint(100, 999))
        card_start_month = datetime.today().strftime('%b %Y')
        current_year = int(datetime.today().strftime('%Y'))
        end_yr = str(current_year + 3)
        card_end_month = datetime.today().strftime('%b')
        card_end_period = card_end_month + ' ' + end_yr
        card_number_prefix = '4568 3579'
        card_number = str(card_number_prefix + ' ' + card_second_last + ' ' +  card_last)
        encode_card_number = encrypt1.encrypt.encode(card_number)
        encode_cvv_number = encrypt1.encrypt.encode(card_cvv)


        
        if username_ln == 0 or name_ln == 0:
            msg = 'Username is blank'
            return render_template("register.html", msg1 = msg)
            
        if db_userlogin.count_documents({ 'userid': username_in }, limit = 1) !=0:
            msg = 'Username '+ username_in + ' Already Taken'
            return render_template("register.html", msg1 = msg)
        if password_in1 != password_in2:
            msg = 'Passwords Doesnt Match'
            return render_template("register.html", msg1 = msg, username = username_in, fullname = name_in, email = email_in) 
        if db_userlogin.count_documents({ 'email': email_in }, limit = 1) !=0:
            msg = 'Email id '+ email_in + ' is already registered'
            return render_template("register.html", msg1 = msg, username = username_in, fullname = name_in) 
        else:
            password_hashed = bcrypt.hashpw(password_in2.encode('utf-8'), bcrypt.gensalt())
            # TO insert User login Details
            db_userlogin.insert_one({'userid': username_in, 'password': password_hashed, 'Name': name_in, 'email': email_in})
            card_name = name_in[0 : 15]
            #To insert Card Details
            db_carddetails.insert_one({'userid': username_in, 'Name': name_in, 'CardName': card_name, 'Cardnum': encode_card_number , 'CardStartdate': card_start_month, 'CardEnddate': card_end_period, 'Cardcvv': encode_cvv_number })
            current_last_account1 = db_userdata.find().sort("_id", -1).limit(1)
            current_userdata = []
            for i in current_last_account1:
                current_userdata.append(i)
            if not current_userdata:
                    # To insert First User Account Details
                    db_userdata.insert_one({"userid": username_in,"Name": name_in,"Accno": "12446001","Accbal":"10000"})
            else:
                #print("current userdata found is: ", current_userdata )
                #print("Current account 1 is : ", current_last_account1)
                new_acc = []
                for i in current_userdata:
                    #print("last account is : ", i)
                    new_acc.append(i["Accno"])
                    last_acc = int(new_acc[0])
                    new_account = str(last_acc + 1)
                    #print("new account inside the loop is: ", new_account)
                # To insert User Account Details
                #print("new account outside the loop is: ", new_account)
                db_userdata.insert_one({"userid": username_in,"Name": name_in,"Accno": new_account ,"Accbal":"10000"})
            msg = 'Registration Sucessful for ' + username_in + ' Please login'
            return render_template('index.html', loginmsg = msg)
    return redirect(url_for('home'))
  
    
@app.route('/login', methods=('GET','POST'))
def login():
    msg = ""
    if session.get('username') is not None:
        #print(" In Route Login session name is true: ", session.get('username'))
        return redirect(url_for('home'))
    else:
        if request.method=='POST':
            session["name"] = request.form.get("username")
            #print(session["name"])
            #print("In session condition")
            username_in = request.form['username']
            password_in = request.form['password']
            username_found = db_userlogin.find_one({'userid': username_in})
            if username_found:
                username_val = username_found['userid']
                passw_check = username_found['password']
                #print("Password is: ",passw_check )
                #print("username is: ", username_val)
                if bcrypt.checkpw(password_in.encode('utf-8'), passw_check):
                    a = ''
                    user_found.append(a)
                    session["username"] = username_val
                    user_found.append(username_found)
                    #print("User found is :", user_found)
                    return redirect(url_for('home'))
                else:
                    msg = 'Wrong password'
                    #print('error: ',msg)
                    return render_template('index.html', loginmsg = msg)
            else:
                if username_in in session:
                    return redirect(url_for('/'))
                msg = 'Invalid username ' + username_in
                return render_template("index.html", loginmsg = msg)    
    return render_template("index.html") 

@app.route("/home",methods=["POST", "GET"])
def home():
    user_session = session.get('username')
    if not user_session:
        #print("In Home functuon username is: ", user_found)
        return render_template('index.html')
    else:
        user_session = session.get('username')
        #print("Session in home new is: ", user_session)
        userdata_found = db_userdata.find_one({'userid': user_session})
        #print("userdata found: ", userdata_found)
        name = userdata_found["Name"]
        Acc_no = userdata_found["Accno"]
        Acc_bal = userdata_found["Accbal"]
        #print("NAme is: ", name)
        return render_template('home.html', username_session = user_session, username = name, Accnumber = Acc_no, Accbalance = Acc_bal, logedin_user = user_session)


@app.route("/onetime-transfer",methods=["POST", "GET"])
def onetime_transfer():    
    user_session = session.get('username')
    if not user_session:
        #print("In Transfer functuon username is: ", user_found)
        return render_template('index.html')
    else:
        user_session = session.get('username')
        userdata_found = db_userdata.find_one({'userid': user_session})
        name = userdata_found["Name"]
        #resp = make_response(render_template('onetime-transfer.html', logedin_user = user_session))
        #resp.headers.update['Referer']= 'onetime-transfer'
        return render_template('onetime-transfer.html', logedin_user = user_session)

@app.route("/transfer",methods=["POST", "GET"])
def transfer():    
    user_session = session.get('username')
    if not user_session:
        #print("In Transfer functuon username is: ", user_found)
        return render_template('index.html')
    else:
        user_beneficiary_found = db_beneficiarydetails.find({'userid':user_session},{"Name","Accno"})
        user_beneficiary_found_list = list(user_beneficiary_found)
        #usr_data = user_data_found["TransID"]
        if not user_beneficiary_found_list:
            #print("No Record Found")
            msg = 'No Beneficiary Found for ' +  user_session + '. Please add Beneficiary or use one time Transfer.'
            return render_template('transfer.html', messages1 = msg, logedin_user = user_session)
        else:
            beneficiary_list1 = []
            msg = 'Please select Account Details to Transfer'
            #print("Transcation found")
            for i in user_beneficiary_found_list:
                del i['_id']
                for j in i.values():
                    beneficiary_list1.append(j)
            #print("type if list is : ", type(beneficiary_list1))
            beneficiary_list = [beneficiary_list1[x:x+2] for x in range(0, len(beneficiary_list1), 2)]
            beni_list_join = list(map(str.join, ('-', '-'), beneficiary_list))
            final_beneficiary_list = [beni_list_join[x:x+1] for x in range(0, len(beni_list_join), 1)]
            return render_template('transfer.html', data = final_beneficiary_list, messages = msg, logedin_user = user_session)

@app.route("/add-beneficiary",methods=["POST", "GET"])
def add_beneficiary():    
    user_session = session.get('username')
    if not user_session:
        #print("In Transfer functuon username is: ", user_found)
        return render_template('index.html')
    else:
        user_session = session.get('username')
        userdata_found = db_userdata.find_one({'userid': user_session})
        return render_template('add-beneficiary.html', logedin_user = user_session)


@app.route("/api/v1/add-beneficiary",methods=["POST", "GET"])
def api_add_beneficiary(): 
    user_session = session.get('username')
    if not user_session:
        #print("In Transfer functuon username is: ", user_found)
        return render_template('index.html')
    else:
        if request.method=='POST':
            accname_in = request.form['accname']
            accnumber_in = request.form['accno']
            accname_found = db_userdata.find_one({'Name': accname_in})
            accnumber_found = db_userdata.find_one({'Accno': accnumber_in})
            current_user_found = db_userdata.find_one({'userid': user_session})
            current_user_name = current_user_found["Name"]
            current_user_accno = current_user_found["Accno"]
            if not accname_found and not accnumber_found:
                msg = "Please Enter Valid Details"
                return render_template('add-beneficiary.html', add_beneficiary_msg = msg, logedin_user = user_session)

            if not accname_found:
                msg = "Account Name not found"
                return render_template('add-beneficiary.html', add_beneficiary_msg = msg, logedin_user = user_session)
            if not accnumber_found:
                 msg = "Account Number not found"
                 return render_template('add-beneficiary.html', add_beneficiary_msg = msg, logedin_user = user_session)
            if current_user_accno == accnumber_found["Accno"]:
                 print("Current user account found is: ", current_user_accno)
                 print("Account number of 3rd party : ", accnumber_found["Accno"] )
                 msg = "Cannnot Add Self Acc as Beneficiary"
                 return render_template('add-beneficiary.html', add_beneficiary_msg = msg, logedin_user = user_session)
            
            if accname_in == accname_found["Name"] and accnumber_in == accnumber_found["Accno"]:
                # Check if already added
                user_beneficary_found = db_beneficiarydetails.find_one({"userid":user_session,"Accno":accnumber_in})
                #print("Current user benificary found is: ", user_beneficary_found)
                if user_beneficary_found:
                    msg =  accnumber_in + " is already added as Beneficiary"
                    return render_template('add-beneficiary.html', add_beneficiary_msg = msg, logedin_user = user_session)
                else:
                    #update current user Beneficiary list
                    db_beneficiarydetails.insert_one({"userid":user_session,"Name":accname_in,"Accno":accnumber_in})
                    return render_template('add-beneficiary-sucess.html', accname=accname_in, accnumber = accnumber_in, logedin_user = user_session)
    return render_template('add-beneficiary.html', logedin_user = user_session)


@app.route("/delete-beneficiary",methods=["POST", "GET"])
def delete_beneficiary(): 
    user_session = session.get('username')
    if not user_session:
        #print("In Transfer functuon username is: ", user_found)
        return render_template('index.html')
    else:
        user_beneficiary_found = db_beneficiarydetails.find({'userid':user_session},{"Name","Accno"})
        user_beneficiary_found_list = list(user_beneficiary_found)
        #usr_data = user_data_found["TransID"]
        if not user_beneficiary_found_list:
            #print("No Record Found")
            msg = 'No Beneficiary Found for ' +  user_session + '. Please add Beneficiary or use one time Transfer.'
            return render_template('delete-beneficiary.html', messages1 = msg, logedin_user = user_session)
        else:
            beneficiary_list1 = []
            msg = 'Please select Beneficiary to delete'
            #print("Transcation found")
            for i in user_beneficiary_found_list:
                del i['_id']
                for j in i.values():
                    beneficiary_list1.append(j)
            #print("type if list is : ", type(beneficiary_list1))
            beneficiary_list = [beneficiary_list1[x:x+2] for x in range(0, len(beneficiary_list1), 2)]
            beni_list_join = list(map(str.join, ('-', '-'), beneficiary_list))
            final_beneficiary_list = [beni_list_join[x:x+1] for x in range(0, len(beni_list_join), 1)]
            return render_template('delete-beneficiary.html', data = final_beneficiary_list, messages = msg, logedin_user = user_session)

@app.route("/api/v1/delete-beneficiary",methods=["POST", "GET"])
def api_delete_beneficiary(): 
    user_session = session.get('username')
    if not user_session:
        #print("In Transfer functuon username is: ", user_found)
        return render_template('index.html')
    else:
        if request.method=='POST':
            user_beneficiary_input = request.form.get('Benificary')
            user_confirmation_input = request.form.get("confirmation")
            if user_beneficiary_input == 'Choose Account:':
                msg = 'Please select Beneficiary'
                return render_template('delete-beneficiary.html', deletemsg = msg, messages = msg, logedin_user = user_session)
            else:
                user_beneficiary_list = user_beneficiary_input.split("-")
                accname_in = user_beneficiary_list[0]
                accnumber_in = user_beneficiary_list[1]
                if user_confirmation_input == 'yes':
                    db_beneficiarydetails.delete_one({"userid":user_session,"Accno":accnumber_in})
                    return render_template('del-beneficiary-sucess.html', accname=accname_in, accnumber = accnumber_in, logedin_user = user_session)
                else:
                    msg = "Please type yes"
                    return render_template('delete-beneficiary.html', messages = msg, deletemsg = msg, logedin_user = user_session)
    return render_template('delete-beneficiary.html')

        


@app.route("/api/v1/onetimetransferfund",methods=["POST", "GET"])
def onetime_transfer_funds(): 
    user_session = session.get('username')
    # To check referrer URL
    """
    url = request.referrer

    print("URl refeere is : ", url)

    url_end = url.split("/")

    url_end_point = url_end[-1]

    if url_end_point == 'onetime-transfer':
        accname_in = request.form['accname']
        accnumber_in = request.form['accno']
        print("From onetime")
    
    if url_end_point == 'transfer':
        print("From Transfer")
    """
    if not user_session:
        #print("In Transfer functuon username is: ", user_found)
        return render_template('index.html')
    else:
        if request.method=='POST':
            accname_in = request.form['accname']
            accnumber_in = request.form['accno']
            transamount_in = request.form['amount']
            accname_found = db_userdata.find_one({'Name': accname_in})
            accnumber_found = db_userdata.find_one({'Accno': accnumber_in})
            current_user_found = db_userdata.find_one({'userid': user_session})
            current_user_name = current_user_found["Name"]
            current_user_accno = current_user_found["Accno"]
            current_date = datetime.today().strftime('%d-%m-%Y')
            current_time = datetime.today().strftime('%H:%M')
            trans_preffix = str(random.randint(999, 10000))
            trans_suffix = str(datetime.today().strftime('%d%m%Y%H%M'))
            trans_id = trans_preffix + trans_suffix
            #trans_complete=[]

            if not accname_found and not accnumber_found and not transamount_in:
                msg = "Please Enter Valid Details"
                return render_template('onetime-transfer.html', transfermsg = msg, logedin_user = user_session)

            if not accname_found:
                msg = "Account Name not found"
                return render_template('onetime-transfer.html', transfermsg = msg, logedin_user = user_session)
            if not accnumber_found:
                 msg = "Account Number not found"
                 return render_template('onetime-transfer.html', transfermsg = msg, logedin_user = user_session)
            if not transamount_in:
                 msg = "Please enter a valid amount"
                 return render_template('onetime-transfer.html', transfermsg = msg, logedin_user = user_session)
            
            if accnumber_in == current_user_found["Accno"]:
                 print("Acc number in is: ",accnumber_in )
                 print("Acc number of current user: ", current_user_found["Accno"] )
                 msg = "Cannot Transfer to Self"
                 return render_template('onetime-transfer.html', transfermsg = msg, logedin_user = user_session)
            
        
            if accname_in == accname_found["Name"] and accnumber_in == accnumber_found["Accno"]:
                current_user_before_bal = float(current_user_found["Accbal"])
                if current_user_before_bal < float(transamount_in):
                    msg = "Insufficient Balance"
                    return render_template('onetime-transfer.html', transfermsg = msg, logedin_user = user_session)
            
                else:
                    end_user_id = accnumber_found["userid"]
                    end_user_name = accnumber_found["Name"]
                    current_bal = accnumber_found["Accbal"]
                    current_user_acc_number = current_user_found["Accno"]
                    Current_user_after_bal = float(float(current_user_before_bal) - float(transamount_in))
                    Transfer_bal = float(float(current_bal) + float(transamount_in))

                    # End User Balance and Transactions Update

                    end_user_acc = { "Accno": accnumber_in }
                    end_user_new_bal = { "$set": { "Accbal": Transfer_bal } }
                    db_userdata.update_one(end_user_acc, end_user_new_bal)

                    accnumber_found = db_userdata.find_one({'Accno': accnumber_in})
                    end_user_updated_bal = accnumber_found["Accbal"]

                    transactions_enduser= end_user_id + 'transactions'
                    db_end_user_transactions = db_name[transactions_enduser]

                    db_end_user_transactions.insert_one({"userid":end_user_id,"Name":end_user_name,"Accno":accnumber_in,"TransID":trans_id,"Fromaccname":current_user_name,"Fromaccno":current_user_accno,"Toaccno":accnumber_in,"Amount":transamount_in,"Transtype":"cr","Date":current_date,"Time":current_time,"Accbal":end_user_updated_bal,"Transdate": datetime.now()})

                    #Current user Balance and Transactions Update
                    current_user_acc = { "Accno": current_user_acc_number }
                    current_user_new_bal = { "$set": { "Accbal": Current_user_after_bal } }

                    transactions_currentuser= user_session + 'transactions'
                    db_current_user_transactions = db_name[transactions_currentuser]
                    db_userdata.update_one(current_user_acc, current_user_new_bal)
                    time.sleep(1)
                    current_user_found = db_userdata.find_one({'userid': user_session})
                    current_user_updated_bal = current_user_found["Accbal"]
                    print("current acc balance after transfer is :", current_user_updated_bal)

                    db_current_user_transactions.insert_one({"userid":user_session,"Name":current_user_name,"Accno":current_user_accno,"TransID":trans_id,"Fromaccname":current_user_name,"Fromaccno":current_user_accno, "Toaccno":accnumber_in,"Amount":transamount_in,"Transtype":"dr","Date":current_date,"Time":current_time,"Accbal":current_user_updated_bal,"Transdate": datetime.now()})
                    return render_template('transfer-sucess.html', transamount = transamount_in, accname=accname_in, accnumber = accnumber_in, transcation_id = trans_id, logedin_user = user_session)
                    
    
    return render_template('onetime-transfer.html', logedin_user = user_session)



@app.route("/api/v1/beneficiarytransferfund",methods=["POST", "GET"])
def beneficiary_transfer_funds(): 
    user_session = session.get('username')
    if not user_session:
        #print("In Transfer functuon username is: ", user_found)
        return render_template('index.html')
    else:
        if request.method=='POST':
            user_beneficiary_input = request.form.get('Benificary')
            transamount_in = request.form['amount']
            user_beneficiary_list = user_beneficiary_input.split("-")
            accname_in = user_beneficiary_list[0]
            accnumber_in = user_beneficiary_list[1]
            accname_found = db_userdata.find_one({'Name': accname_in})
            accnumber_found = db_userdata.find_one({'Accno': accnumber_in})
            current_user_found = db_userdata.find_one({'userid': user_session})
            current_user_name = current_user_found["Name"]
            current_user_accno = current_user_found["Accno"]
            current_date = datetime.today().strftime('%d-%m-%Y')
            current_time = datetime.today().strftime('%H:%M')
            trans_preffix = str(random.randint(999, 10000))
            trans_suffix = str(datetime.today().strftime('%d%m%Y%H%M'))
            trans_id = trans_preffix + trans_suffix
            #trans_complete=[]

            if not accname_found and not accnumber_found and not transamount_in:
                msg = "Please Enter Valid Details"
                return render_template('transfer.html', transfermsg = msg, logedin_user = user_session)

            if not accname_found:
                msg = "Account Name not found"
                return render_template('transfer.html', transfermsg = msg, logedin_user = user_session)
            if not accnumber_found:
                 msg = "Account Number not found"
                 return render_template('transfer.html', transfermsg = msg, logedin_user = user_session)
            if not transamount_in:
                 msg = "Please enter a valid amount"
                 return render_template('transfer.html', transfermsg = msg, messages = msg, logedin_user = user_session)
            
            if accnumber_in == current_user_found["Accno"]:
                 print("Acc number in is: ",accnumber_in )
                 print("Acc number of current user: ", current_user_found["Accno"] )
                 msg = "Cannot Transfer to Self"
                 return render_template('transfer.html', transfermsg = msg, logedin_user = user_session)
            
        
            if accname_in == accname_found["Name"] and accnumber_in == accnumber_found["Accno"]:
                current_user_before_bal = float(current_user_found["Accbal"])
                if current_user_before_bal < float(transamount_in):
                    msg = "Insufficient Balance"
                    return render_template('transfer.html', transfermsg = msg, logedin_user = user_session)
            
                else:
                    end_user_id = accnumber_found["userid"]
                    end_user_name = accnumber_found["Name"]
                    current_bal = accnumber_found["Accbal"]
                    current_user_acc_number = current_user_found["Accno"]
                    Current_user_after_bal = float(float(current_user_before_bal) - float(transamount_in))
                    Transfer_bal = float(float(current_bal) + float(transamount_in))

                    # End User Balance and Transactions Update
                    end_user_acc = { "Accno": accnumber_in }
                    end_user_new_bal = { "$set": { "Accbal": Transfer_bal } }
                    db_userdata.update_one(end_user_acc, end_user_new_bal)

                    accnumber_found = db_userdata.find_one({'Accno': accnumber_in})
                    end_user_updated_bal = accnumber_found["Accbal"]

                    transactions_enduser= end_user_id + 'transactions'
                    db_end_user_transactions = db_name[transactions_enduser]

                    db_end_user_transactions.insert_one({"userid":end_user_id,"Name":end_user_name,"Accno":accnumber_in,"TransID":trans_id,"Fromaccname":current_user_name,"Fromaccno":current_user_accno,"Toaccno":accnumber_in,"Amount":transamount_in,"Transtype":"cr","Date":current_date,"Time":current_time,"Accbal":end_user_updated_bal,"Transdate": datetime.now()})

                    #Current user Balance and Transactions Update
                    current_user_acc = { "Accno": current_user_acc_number }
                    current_user_new_bal = { "$set": { "Accbal": Current_user_after_bal } }
                    transactions_currentuser= user_session + 'transactions'
                    db_current_user_transactions = db_name[transactions_currentuser]
                    db_userdata.update_one(current_user_acc, current_user_new_bal)
                    time.sleep(1)
                    current_user_found = db_userdata.find_one({'userid': user_session})
                    current_user_updated_bal = current_user_found["Accbal"]
                    print("current acc balance after transfer is :", current_user_updated_bal)

                    db_current_user_transactions.insert_one({"userid":user_session,"Name":current_user_name,"Accno":current_user_accno,"TransID":trans_id,"Fromaccname":current_user_name,"Fromaccno":current_user_accno, "Toaccno":accnumber_in,"Amount":transamount_in,"Transtype":"dr","Date":current_date,"Time":current_time,"Accbal":current_user_updated_bal,"Transdate": datetime.now()})
                    return render_template('transfer-sucess.html', transamount = transamount_in, accname=accname_in, accnumber = accnumber_in, transcation_id = trans_id, logedin_user = user_session)
    
    return render_template('onetime-transfer.html', logedin_user = user_session)



@app.route("/recent-transactions",methods=["POST", "GET"])
def recent_trans(): 
    user_session = session.get('username')
    if not user_session:
        #print("In Transfer functuon username is: ", user_found)
        return render_template('index.html')
    else:

        user_session = session.get('username')
        transactions_currentuser= user_session + 'transactions'
        db_current_user_transactions = db_name[transactions_currentuser]
        #user_data_found = db_transactions.find({'userid':user_session},{"TransID","Fromaccname","Fromaccno","Toaccno","Amount","Transtype","Date","Time","Accbal"}).limit(10).sort("TransID",-1)
        user_data_found = db_current_user_transactions.find({'userid':user_session},{"TransID","Fromaccname","Fromaccno","Toaccno","Amount","Transtype","Date","Time","Accbal"},   sort=[( '_id', pymongo.DESCENDING )] ).limit(10)
        
        user_data_found_list = list(user_data_found)
        #usr_data = user_data_found["TransID"]
        ##print("Use Data in recent trans: ",usr_data)
        if not user_data_found_list:
            #print("No Record Found")
            msg = 'No Transcation found for ' +  user_session
            return render_template('recent-transactions.html', messages1 = msg, logedin_user = user_session)
        else:
            trans_list1 = []
            msg = 'Recent Transcations of ' + user_session
            #print("Transcation found")
            for i in user_data_found_list:
                del i['_id']
                for j in i.values():
                    trans_list1.append(j)
            ##print(trans_list1)
            trans_list = [trans_list1[x:x+9] for x in range(0, len(trans_list1), 9)]
            ##print(trans_list)
            return render_template('recent-transactions.html', data = trans_list, messages = msg, logedin_user = user_session)


@app.route("/detailed-transactions",methods=["POST", "GET"])
def details_trans(): 
    user_session = session.get('username')
    if not user_session:
        #print("In Transfer functuon username is: ", user_found)
        return render_template('index.html')
    else:
        return render_template('detailed-transactions.html',logedin_user = user_session)


@app.route("/api/v1/detailed-transactions",methods=["POST", "GET"])
def api_detailed_trans(): 
    user_session = session.get('username')
    if not user_session:
        #print("In Transfer functuon username is: ", user_found)
        return render_template('index.html')
    else:
        if request.method=='POST':
            user_required_input = request.form.get('months')
            current_user_found = db_userdata.find_one({'userid': user_session})
            current_user_name = current_user_found["Name"]
            current_user_accno = current_user_found["Accno"]
            current_user_accbal = current_user_found["Accbal"]
            transactions_currentuser= user_session + 'transactions'
            db_current_user_transactions = db_name[transactions_currentuser]
            today = datetime.today()
            current_month = str(today.strftime('%m'))
            end_required_month = int(current_month) - int(user_required_input)
            end_month = today - relativedelta(month=end_required_month)
            search_year = int(datetime.strftime(end_month, '%Y'))
            search_month = int(datetime.strftime(end_month, '%m'))
            search_date = int(datetime.strftime(end_month, '%d'))
            from_date = datetime.strftime(end_month, '%d-%b-%Y')
            current_date = datetime.today().strftime('%d-%b-%Y')

            file_path = 'statements/' + user_session + '_' + current_date + '.csv'

            myquery = db_current_user_transactions.find({ "Transdate": {"$gt": datetime(search_year, search_month, search_date)}}, {"TransID","Fromaccname","Fromaccno","Toaccno","Amount","Transtype","Date","Time","Accbal"})

            #myquery = db_current_user_transactions1.find({ "Transdate:": {"$gt": datetime(2022, 9, 17)}}, {"TransID","Fromaccname","Fromaccno","Toaccno","Amount","Transtype","Date","Time","Accbal"})
            
            statement_path = os.getenv("Statement_dir")

            #file =  'r' + "'" + statement_path + user_session + '*' + '.csv' + "'"
            
            file = statement_path + user_session + '*.csv'
            
            file_csv_name = statement_path + user_session + '_' + current_date + '.csv'
            
            fileList = glob.glob(file, recursive=True)
            for file in fileList:
                os.remove(file)
            
            file = open(file_csv_name, 'w')
            output = csv.writer(file) # writng in this file

            Name = ['Name', current_user_name]
            Acc_number = ['Acc No', current_user_accno]
            Acc_bal = ['Acc Balance', current_user_accbal]
            frm_date =['From Date', from_date]
            to_date = ['To Date', current_date]
            heading = ["Transcation ID", "From Acc no",	"To Acc no", "Amount", "Remarks", "Type", "Date", "Time", "Account Balance"]

            output.writerow(Name)
            output.writerow(Acc_number)
            output.writerow(Acc_bal)
            output.writerow(frm_date)
            output.writerow(to_date)
            output.writerow(heading)
            trans_list = []
            for i in myquery:
                del i['_id']
                for j in i.values():
                    trans_list.append(j)
            trans_list1 = [trans_list[x:x+9] for x in range(0, len(trans_list), 9)]

            for row in trans_list1:
                output.writerow(row)  

            file.close()
            return send_file(file_csv_name, mimetype='text/csv', as_attachment=True)

@app.route("/cards",methods=["POST", "GET"])
def cards(): 
    user_session = session.get('username')
    if not user_session:
        #print("In Transfer functuon username is: ", user_found)
        return render_template('index.html')
    else:
        user_session = session.get('username')
        card_details_found = db_carddetails.find_one({'userid': user_session})
        #print("Card Details found is: ", card_details_found)
        card_number = card_details_found["Cardnum"]
        card_start_date = card_details_found["CardStartdate"]
        card_end_date = card_details_found["CardEnddate"]
        card_holder_name = card_details_found["CardName"]
        card_cvv_num = card_details_found["Cardcvv"]
        decoded_card_number = encrypt1.encrypt.decode(card_number)
        decode_cvv_number = encrypt1.encrypt.decode(card_cvv_num)
        return render_template('cards.html', card_num = decoded_card_number, card_start = card_start_date, card_end = card_end_date, card_name = card_holder_name,card_cvv = decode_cvv_number, logedin_user = user_session)

@app.route("/logout",methods=["POST", "GET"])
def logout():
    session.pop("username", None)
    session.clear()
    return redirect("/")

app.run()

