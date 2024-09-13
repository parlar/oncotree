#!/usr/bin/env python 

import pandas as pd
import argparse
import json
from pprint import pprint


levels = ["level_" + str(i) for i in range(1, 8)]
meta_cols = ["metamaintype","metacolor","metanci","metaumls"]


def get_keylist(row):
    """
    Given a row in a dataframe, construct a list of the level 1-7 values
    (i.e., the tumor type hierarchy) if they are strings.
    """
    key_list = []
    for level in levels:
        tumor_type = row[level]
        if isinstance(tumor_type, str):
            key_list.append(tumor_type)
        else:
            break
    return key_list


def tumor_type_hierarchy_simple(dataframe):
    """Builds a nested dictionary hierarchy from a list of lists of tumor types."""
    tumor_type_lists = []
    for _, row in dataframe.iterrows():
        tumor_type_list = get_keylist(row)
        if len(tumor_type_list) > 1:
            tumor_type_lists.append(tumor_type_list)

    hierarchy = {}
    for tumor_type_list in tumor_type_lists:
        current = hierarchy
        for tumor_type in tumor_type_list:
            if tumor_type not in current:
                current[tumor_type] = {}
            current = current[tumor_type]
    return hierarchy

def mk_object(name, maintype, color, nci, umls):
    return {"name": name, "metamaintype": maintype, "color": color, "nci": nci, "umls": umls, "children": []}


def add_child_by_parent_name(data, parent_name, new_child):
    """
    Adds `new_child` to the children of the node with name `parent_name` in `data`.
    Returns True if the node was found, False otherwise.
    """
    def _traverse_and_add(node):
        if node['name'] == parent_name:
            node.setdefault('children', []).append(new_child)
            return True
        if 'children' in node:
            for child in node['children']:
                if _traverse_and_add(child):
                    return True
        return False

    return any(_traverse_and_add(item) for item in data)


def tumor_type_hierarchy(dataframe):
    """Build a nested list of objects from a pandas DataFrame."""
    hierarchy = []
    for _, row in dataframe.iterrows():
        keylist = get_keylist(row)
        if len(keylist) == 1:
            hierarchy.append(mk_object(keylist[0], row["metamaintype"], row["metacolor"], row["metanci"], row["metaumls"]))
        else:
            add_child_by_parent_name(hierarchy, keylist[-2], mk_object(keylist[-1], row["metamaintype"], row["metacolor"], row["metanci"], row["metaumls"]))
    return hierarchy


def main():
    parser = argparse.ArgumentParser(description='Convert OncoTree file to JSON.')
    
    parser.add_argument('input_file', help='Path to the input oncotree file')
    parser.add_argument('-o', '--output_file', help='Path to the output file', required=False)
    parser.add_argument('--format', choices=['simple', 'object'], default='simple', help='Format for the output file (simple json or object json)')
    
    args = parser.parse_args()
    
    with open(args.input_file, 'r') as input_file:
        dataframe = pd.read_csv(input_file, sep='\t')

    if args.format == 'object':
        data = tumor_type_hierarchy(dataframe)
    elif args.format == 'simple':
        data = tumor_type_hierarchy_simple(dataframe)
    else:
        raise ValueError(f'Invalid format: {args.format}')

    if args.output_file:
        with open(args.output_file, 'w') as output_file:
            json.dump(data, output_file)
    else:
        print(json.dumps(data, indent=4))

 
if __name__ == '__main__':
    main()
