from __future__ import annotations
from functools import lru_cache
from anytree import Node, RenderTree, NodeMixin
from anytree.exporter import DotExporter
import pandas as pd
import numpy as np
from pathlib import Path
import graphviz
import json

BASE_DIR = Path('.')


def calculate_customer_features(customer_data):
    data_dict = {}
    # print(customer_data['total_credit'])
    if customer_data['total_credit'] is None:
        data_dict[0] = 'There is no data'
    elif customer_data['total_credit'] != 0:
        data_dict[0] = 'yes'
    else:
        data_dict[0] = 'no'

    if customer_data['total_tomorrow_account_balance'] is None:
        data_dict[1] = 'There is no data'
    elif customer_data['total_tomorrow_account_balance'] != 0:
        data_dict[1] = 'yes'
    else:
        data_dict[1] = 'no'

    if customer_data['account_status_is_active'] is None or customer_data['account_status_is_valid'] is None:
        data_dict[2] = 'There is no data'
    elif customer_data['account_status_is_active'] and customer_data['account_status_is_valid']:
        data_dict[2] = 'yes'
    else:
        data_dict[2] = 'no'

    if customer_data['bank_title'] is None:
        data_dict[3] = 'There is no data'
    elif customer_data['bank_title'] == 'tejarat':
        data_dict[3] = 'yes'
    else:
        data_dict[3] = 'no'

    if customer_data['account_number'] is None:
        data_dict[4] = 'There is no data'
    elif customer_data['account_number'].startswith('000'):
        data_dict[4] = 'yes'
    else:
        data_dict[4] = 'no'

    if customer_data['customer_access_to_account_number'] is None:
        data_dict[5] = 'There is no data'
    elif customer_data['customer_access_to_account_number']:
        data_dict[5] = 'yes'
    else:
        data_dict[5] = 'no'

    if customer_data['sales_record_date'] is None or customer_data['response_date'] is None:
        data_dict[6] = 'There is no data'
    elif customer_data['sales_record_date'] == customer_data['response_date']:
        data_dict[6] = 'yes'
    else:
        data_dict[6] = 'no'

    return data_dict


class FeatureNodeClass(NodeMixin):  # Add Node feature
    def __init__(self, _name, _id, node_type: dict[str, int], parent: FeatureNodeClass = None, parent_value = None, color = None , shape = None):
        super(FeatureNodeClass, self).__init__()
        self.name = f"edge_value : {parent_value}\n node_id : {_id} \n {_name[0:round(len(_name)/2)]}\n {_name[round(len(_name)/2):]}..."
        self.id = _id
        self.node_type = node_type
        self.parent: FeatureNodeClass = parent
        self.parent_value = parent_value
        self.color = color
        self.shape = shape

    @property
    def is_leaf(self):
        return self.node_type['type'] == 'response'

    @lru_cache
    def get_ancestors_values(self):
        if self.parent:
            return {**self.parent.get_ancestors_values(), self.parent.node_type['id']: self.parent_value}
        else:
            return {}


def get_parent_node(tree_nodes, node):
    for n in tree_nodes:
        if n.id == node['parent_id']:
            return n
    return None

# def get_parent_type():
#     nod = None
#     for i in tree_nodes:
#         if i.parent:
#             if i.parent.id == node['parent_id']:
#                 nod = i
#                 break
#     return nod


def make_tree():
    # load response_info
    response_info = pd.read_excel('responses_info.xlsx')
    response_info = response_info.set_index(['id'])

    # load feature_info
    feature_info = pd.read_excel('features_info.xlsx')
    feature_info = feature_info.set_index(['id'])

    # reading tree nodes data
    with open('tree_taghazaye_vajh.json', 'r') as tree_json:
        tree_json = json.load(tree_json)

    tree_nodes = []
    for n in tree_json['tree_nodes']:
        if n['node_type']['type'] == 'feature':
            name = feature_info.loc[n['node_type']['id'], 'feature_eng_name'][0:100]
            color = 'red'
            shape = 'oval'
        elif n['node_type']['type'] == 'response':
            name = response_info.loc[n['node_type']['id'], 'response_content'][0:100]
            color = 'blue'
            shape = 'square'
        else:
            name = ''
            shape = 'circle'
            color = "yellow"
        parent_node = get_parent_node(tree_nodes, n)
        tree_nodes.append(
            FeatureNodeClass(name, n['id'], n['node_type'], parent=parent_node, parent_value=n['parent_value'],
                             color=color, shape=shape))

    return tree_nodes


def get_leaf_nodes(tree_nodes):

    # extract leaf nodes
    leaf_nodes = []
    for pre, fill, node in RenderTree(tree_nodes[0]):
        if node.is_leaf:
            leaf_nodes.append(node)
    return leaf_nodes


def get_response(tree_nodes, customer_features):
    leaf_nodes = get_leaf_nodes(tree_nodes)
    response = ''
    for node in leaf_nodes:
        for index, val in node.get_ancestors_values().items():
            if customer_features[index] != val:
                break
        else:
            response = node.node_type
    return response


def set_color_shape(node):
    attrs = []
    attrs += [f'color={node.color}'] if hasattr(node, 'color') else []
    attrs += [f'shape={node.shape}'] if hasattr(node, 'shape') else []
    return ', '.join(attrs)


def save_data_tree(tree_nodes, name):
    DotExporter(tree_nodes[0]).to_dotfile(f"{name}.dot")
    DotExporter(tree_nodes[0], nodeattrfunc=set_color_shape).to_picture(f"{name}.png")



