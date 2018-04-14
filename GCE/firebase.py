import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import socket
import time
#https://github.com/firebase/quickstart-python/blob/master/db/index.py
#https://stackoverflow.com/questions/40984433/python-firebase-listener-implementation

database_url = 'https://coin-temple.firebaseio.com/'
PATH_TO_JSON = 'settings/firebase-creds.json'

service_account = PATH_TO_JSON
cred = credentials.Certificate(service_account)
firebase_admin.initialize_app(cred, {
    'databaseURL': database_url
})

def set_in_firebase(list_of_keys, value_to_set):
    path_string = "/".join(list_of_keys[:-1])
    ref = db.reference(path_string)
    ref.set({
        list_of_keys[-1]: value_to_set
    })
    #firebase_admin.delete_app(firebase_admin.get_app())

def firebase_push_value(list_of_keys, value_to_set):
    path_string = "/".join(list_of_keys)
    posts_ref = db.reference(path_string)
    # [START push_value]
    new_post_ref = posts_ref.push(value_to_set)
    #new_post_ref.set(value_to_set)


def set_child_value(list_of_keys, value_to_set):

    path_string = "/".join(list_of_keys[:-1])

    close_ref = db.reference("/".join(list_of_keys[:-1]))
    close_ref.child(list_of_keys[-1]).set(value_to_set)


def get_reference():
    # [START get_reference]
    # Import database module.

    # Get a database reference to our blog.
    ref = db.reference('server/saving-data/fireblog')
    # [END get_reference]
    print(ref.key)


def set_value():
    ref = db.reference('server/saving-data/fireblog')

    # [START set_value]
    users_ref = ref.child('users')
    users_ref.set({
        'alanisawesome': {
            'date_of_birth': 'June 23, 1912',
            'full_name': 'Alan Turing'
        },
        'gracehop': {
            'date_of_birth': 'December 9, 1906',
            'full_name': 'Grace Hopper'
        }
    })
    # [END set_value]



def update_child():
    ref = db.reference('server/saving-data/fireblog')
    users_ref = ref.child('users')

    # [START update_child]
    hopper_ref = users_ref.child('gracehop')
    hopper_ref.update({
        'nickname': 'Amazing Grace'
    })
    # [END update_child]

def update_children():
    ref = db.reference('server/saving-data/fireblog')
    users_ref = ref.child('users')

    # [START update_children]
    users_ref.update({
        'alanisawesome/nickname': 'Alan The Machine',
        'gracehop/nickname': 'Amazing Grace'
    })
    # [END update_children]

def overwrite_value():
    ref = db.reference('server/saving-data/fireblog')
    users_ref = ref.child('users')

    # [START overwrite_value]
    users_ref.update({
        'alanisawesome': {
            'nickname': 'Alan The Machine'
        },
        'gracehop': {
            'nickname': 'Amazing Grace'
        }
    })
    # [END overwrite_value]

def firebase_read_value(list_of_keys):
    # [START read_value]
    # Get a database reference to our posts
    path_string = "/".join(list_of_keys)
    ref = db.reference(path_string)
    # Read the data at the posts reference (this is a blocking operation)
    return ref.get()
    # [END read_value]



"""
#get_reference()
set_value()
set_child_value()
update_child()
update_children()
overwrite_value()
push_value()
read_value()
"""

