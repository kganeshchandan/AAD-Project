# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

import sys  
sys.path.append('../../codes')

from flask import jsonify, render_template, redirect, request, url_for
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)

from app.codes.ecdsa_string import *
from app.codes.SHA256 import *
import random
from app import db, login_manager
from app.base import blueprint
from app.base.forms import LoginForm, CreateAccountForm, MakeTransactionCrypto
from app.base.models import User, User_Crypto, Public_Ledger, Transaction_Crypto

from app.base.util import verify_pass

@blueprint.route('/')
def route_default():
    return redirect(url_for('base_blueprint.login'))

@blueprint.route('/error-<error>')
def route_errors(error):
    return render_template('errors/{}.html'.format(error))

## Login & Registration

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:
        
        # read form data
        username = request.form['username']
        password = request.form['password']

        # Locate user
        user = User.query.filter_by(username=username).first()
        
        # Check the password
        if user and verify_pass( password, user.password):

            login_user(user)
            return redirect(url_for('base_blueprint.route_default'))

        # Something (user or pass) is not ok
        return render_template( 'accounts/login.html', msg='Wrong user or password', form=login_form)

    if not current_user.is_authenticated:
        return render_template( 'accounts/login.html',
                                form=login_form)
    return redirect(url_for('home_blueprint.index'))

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    login_form = LoginForm(request.form)
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username  = request.form['username']
        email     = request.form['email'   ]

        user = User.query.filter_by(username=username).first()
        if user:
            return render_template( 'accounts/register.html', msg='Username already registered', form=create_account_form)

        user = User.query.filter_by(email=email).first()
        if user:
            return render_template( 'accounts/register.html', msg='Email already registered', form=create_account_form)

        # else we can create the user
        user = User(**request.form)
        db.session.add(user)
        db.session.commit()

        return render_template( 'accounts/register.html', msg='User created please <a href="/login">login</a>', form=create_account_form)

    else:
        return render_template( 'accounts/register.html', form=create_account_form)

@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('base_blueprint.login'))

@blueprint.route('/shutdown')
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'


# implementations

@blueprint.route('/register_for_crypto', methods=['GET','POST'])
def register_for_crypto():

    if not current_user.is_authenticated:
        return redirect(url_for('base_blueprint.login'))

    if request.method == "POST":

        current_username = current_user._get_current_object().username

        if User_Crypto.query.filter_by(username=current_username).first():
           return render_template('views/pay.html', msg='Already Registered!') 


        pvk, pbk = generate_KeyPair()
        id = User.query.filter_by(username=current_username).first().id
       # print(type(pvk), type(pbk), id)
        user = User_Crypto(current_username, pvk, pbk, id)
        db.session.add(user)
        db.session.commit()


        return render_template('views/pay.html', msg='Registered!')
    else:
        return render_template('views/pay.html')


@blueprint.route('public_ledger', methods=['GET'])
def showTable():
    N = 10

    prev_hash = 0x00

    for i in range(N):
        pbk_sender = generate_KeyPair()[1]
        pvk_sender = generate_KeyPair()[0]
        pbk_receiver = generate_KeyPair()[1]
        amount = str(random.randint(10,999))
        date = '31/10/2020'
        comments = 'hahah'

        message = pbk_sender + pbk_receiver + amount + date + comments
        
        digital_signature = create_Signature(message, pvk_sender) 
        
        nonce = str(random.randint(10,999))   # to be determined externallysssss

        current_hash = SHA256(message + digital_signature + nonce)
        

        data = Public_Ledger(pbk_sender,pbk_receiver,pvk_sender,amount,date,comments,prev_hash,current_hash,nonce,digital_signature)
        
        prev_hash = current_hash
       
        db.session.add(data)
        db.session.commit() 

    return render_template('views/pay.html',msg='populated!')

@blueprint.route('make_transaction_aaa', methods=['GET','POST'])
def createTransaction():

    if not current_user.is_authenticated:
        return redirect(url_for('base_blueprint.login'))

    if request.method == "POST":
        print("print stuff!")

        form = MakeTransactionCrypto(request.form)

        # print(form['private_key'])
        
        if request.form:
            print("scatter!")
            # public_key = form.public_key.data
            # private_key = form.private_key.data
            
            private_key, public_key = generate_KeyPair()
            
            amount = str(form.amount.data)         # integer
            receiver_public_key = form.receiver_public_key.data
            comments = form.comments.data

        # prev_hash = Public_Ledger.query.order_by(id.desc()).first().current_hash   -----> add after mining

            #date = date.today().strftime("%d/%m/%Y")
            date = '10/10/2021'
            message = public_key + receiver_public_key + amount + date + comments
            digital_sig = create_Signature(message, private_key)

            data = Transaction_Crypto(public_key, receiver_public_key, amount, date, comments, digital_sig)

            print("scatter2!")

            db.session.add(data)
            db.session.commit() 

    
    return render_template('views/make_transaction.html', form=MakeTransactionCrypto)


## Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('errors/403.html'), 403

@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('errors/403.html'), 403

@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500
