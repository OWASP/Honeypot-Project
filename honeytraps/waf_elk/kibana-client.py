#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime
from elasticsearch import Elasticsearch
import json
import time
from pymisp import PyMISP
from keys import misp_url, misp_key, misp_verifycert

class MispEvent(object):
    #### Create an event on MISP

    ##Event consists of distribution, information, analysis and threat

    # The distribution setting used for the attributes and for the newly created event, if relevant. [0-3].

    distrib = 0

    # Used to populate the event info field if no event ID supplied.

    info = 'This is event generated from PyMISP'

    # The analysis level of the newly created event, if applicable. [0-2]

    analysis = 0

    # The threat level ID of the newly created event, if applicable. [1-4]

    threat = 1

    """docstring for MispEvent"""
    def __init__(self, distribution,info,analysis,threat):
        super(MispEvent, self).__init__()
        self.distrib = distribution
        self.info = info
        self.analysis = analysis
        self.threat = threat
        

def init(url, key):
    return PyMISP(url, key, misp_verifycert, 'json', debug=True)


def generate_event_info(json_log):
    attacker_ip_address = json.dumps(json_log['_source']['transaction']['remote_address'])
    transaction_time = json.dumps(json_log['_source']['transaction']['time'])
    audit_data = json.dumps(json_log['_source']['audit_data']['messages'])
    audit_data_producer = json.dumps(json_log['_source']['audit_data']['producer'])

    event_info = "Attack identified from the "+attacker_ip_address+" at timestamp "+transaction_time+"  "+audit_data+" This information is generated from "+audit_data_producer
    return event_info


def generate_misp_event(misp_event):
    misp = init(misp_url, misp_key)
    event = misp.new_event(misp_event.distrib, misp_event.threat, misp_event.analysis, misp_event.info)
    misp.add_tag(event, 'AutoGenerated', attribute=False)
    misp.add_tag(event, 'HoneytrapEvent', attribute=False)
    misp.add_tag(event, 'ModSecurity', attribute=False)
    print(event)


def generate_misp_tags():
    misp = init(misp_url, misp_key)
    misp.new_tag(name='AutoGenerated', colour='#00ace6', exportable=True)
    misp.new_tag(name='HoneytrapEvent', colour='#581845', exportable=True)
    misp.new_tag(name='ModSecurity', colour='#a04000', exportable=True)



es = Elasticsearch()

index_name = ""

watch_interval = 10  # seconds

for index in es.indices.get('*'):
    print(index)
    index_str = str(index) 
    if index_str.find("filebeat-") != -1:
        print("found it!")
        print(index_str)
        index_name = index_str
        break

generate_misp_tags()

while True:
    res = es.search(index=index_name,
                    body={'query':{'range':{
                           '@timestamp':{
                                    'gte':'now-'+str(watch_interval)+'s',
                                    'lt':'now'
                            }
                    }}
                    })

    print('Got %d Hits:' % res['hits']['total']['value'])

    for hit in res['hits']['hits']:
        # print(hit)
        json_log = hit
        print('Index is ' + json_log['_index'])
        misp_event_info = generate_event_info(json_log)
        misp_event_obj = MispEvent(0,misp_event_info,0,1)
        print('=====================================================')
        generate_misp_event(misp_event_obj)
    time.sleep(watch_interval)