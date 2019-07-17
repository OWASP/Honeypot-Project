#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pymisp import PyMISP
from keys import misp_url, misp_key, misp_verifycert


def init(url, key):
    return PyMISP(url, key, misp_verifycert, 'json', debug=True)

if __name__ == '__main__':

    #### Create an event on MISP

    ##Event consists of distribution, information, analysis and threat

    #The distribution setting used for the attributes and for the newly created event, if relevant. [0-3].
    distrib = 0

    #Used to populate the event info field if no event ID supplied.
    info = "This is event generated from PyMISP"
    
    #The analysis level of the newly created event, if applicable. [0-2]
    analysis = 0

    #The threat level ID of the newly created event, if applicable. [1-4]
    threat = 1

    misp = init(misp_url, misp_key)
    
    event = misp.new_event(distrib, threat, analysis, info)

    tag = "Sample-Tag"
    misp.add_tag(event, tag, attribute=False)

    new_tag = "AutoGen-Tag"
    misp.new_tag(name=new_tag, colour='#00ace6', exportable=True)
    
    misp.add_tag(event, new_tag, attribute=False)
    print(event)
