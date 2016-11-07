#    Delay Controller UI for the M1686 Digital Delay Generator
#    Copyright (C) 2013-2014 Kiran Majer, Nico Klausner
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''
Module providing low level file storage methods:
    state_dict  ->  xml-|pickle-file
    xml-|pickle-file  ->  state_dict
    
Can be imported by other modules to extract data from state files.  
'''
from pickle import dump, load
from lxml import etree
import json


def save_pickle(filepath, state_dict):
    '''Dumps <state_dict> to a pickle file with <filepath>'''
    with open(filepath, 'wb') as f:
        dump(state_dict, f)

def save_json(filepath, state_dict):
    '''Dumps <state_dict> to a json file with <filepath>'''
    with open(filepath, 'w') as f:
        json.dump(state_dict, f, sort_keys=True, indent=4, separators=(',', ': '))    

def save_xml(filepath, state_dict):
    '''Dumps <state_dict> to a xml file with <filepath>.
    Following structure is allowed (for now), i.e. can be reproduced
    by __load_xml:
    1. level:   key:    str
                value:  [str, int, float, dict]
    2. level:   key:    str
                value:  [str, int ,float, list, bool]
    Whereas nested types only must contain non-nested types '''
    # building xml structure
    'TODO: handle id and maybe version'
    xml_root = etree.Element('delayui_state', id='casi delay 1')
    xml_statedict = etree.SubElement(xml_root, 'dict')
    for k, v in state_dict.items():
    #xml_list = etree.SubElement(xml_root, 'list')
    # dumping list and status dicts
    #for status_dict in status_list:
        xml_statedictentry = etree.SubElement(xml_statedict, 'dict_entry')
        xml_key = etree.SubElement(xml_statedictentry, 'key')
        xml_key.attrib['type'] = 'str'
        xml_key.text = k
        xml_value = etree.SubElement(xml_statedictentry, 'value')
        xml_value.attrib['type'] = type(v).__name__
        if type(v) is dict:
            xml_dict = etree.SubElement(xml_value, 'dict')
            for ke, va in v.items():
                xml_dictentry = etree.SubElement(xml_dict, 'dict_entry')
                xml_key = etree.SubElement(xml_dictentry, 'key')
                xml_key.attrib['type'] = 'str'
                xml_key.text = ke
                xml_value = etree.SubElement(xml_dictentry, 'value')
                xml_value.attrib['type'] = type(va).__name__
                xml_value.text = str(va)
        else:
            xml_value.text = str(v)

    #print(etree.tostring(xml_root, pretty_print=True, encoding='unicode'))
    tree = etree.ElementTree(xml_root)
    with open(filepath, 'wb') as f:
        tree.write(f, encoding='UTF-8', pretty_print=True, compression=0)


def load_pickle(filepath):
    '''Reads the pickle file with <filepath> and returns contents as a state_dict.'''
    with open(filepath, 'rb') as f:
        state_dict = load(f)
    return state_dict

def load_json(filepath):
    '''Reads the json file with <filepath> and returns contents as a state_dict.'''
    with open(filepath, 'r') as f:
        state_dict = json.load(f)
    return state_dict
    
def load_xml(filepath):
    '''Reads the xml file with <filepath> and returns contents as a state_dict.'''
    def str_to_list(a_str):
        if a_str == '[]':
            return []
        else:
            return [int(i) for i in a_str[1:-1].split(',')]
        
    def str_to_bool(a_str):
        if a_str == 'True':
            return True
        elif a_str == 'False':
            return False
        else:
            raise ValueError('Unknown string. Conversion works only with "True" and "False".')
    
    type_map = {'str': str,
                'int': int,
                'float': float,
                'list': str_to_list,
                'bool': str_to_bool}
    
    state_dict = {}
            
    with open(filepath, 'rb') as f:
        xml_tree = etree.parse(f)
    xml_root = xml_tree.getroot()
    xml_statedict = xml_root.find('dict')
    for dict_entry in xml_statedict:
        k = dict_entry.find('key').text
        vt = dict_entry.find('value').attrib['type']
        #print('type of vt: ', type(vt))
        #print('found entry with key: {} and value of type: {}'.format(k, vt))
        if 'dict' in vt:
            #print('parsing dict ...')
            d = {}
            xml_dict = dict_entry.find('value').find('dict')
            for dict_entry in xml_dict:
                ke = dict_entry.find('key').text
                vt = dict_entry.find('value').attrib['type']
                vs = dict_entry.find('value').text
                va = type_map[vt](vs)
                d[ke] = va
            v = d
        else:
            #print('not a dict, parsing value ...')
            vs = dict_entry.find('value').text
            v = type_map[vt](vs)
        state_dict[k] = v

    return state_dict
    

