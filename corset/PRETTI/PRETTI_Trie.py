class Node: 
    def __init__(self, e):
        self.v_list = set()
        self.children = dict() 


class PTrie:
    def __init__(self, InvInd: list, n_rows: int):
        self._root = Node(e=None)
        self._root.v_list = set([x for x in range(n_rows)])
        self.InvInd = InvInd
        self.trie_new_rows = [[] for _ in range(n_rows)]


    #def get_children(current_node, a): 
    #    for child in current_node.children: 
    #        if child.v==a: 
    #            return child 
    #    return None 
        

    # def ProcessRecord(self, r_id: int, a_set: set, ordering: list):
    #     ''' build trie on-the-fly while processing records''' 
        
    #     # we first sort the attributes by the pre-computed frequency ordering 
    #     a_list = [x for x in ordering if x in a_set] 
    #     current_node = self._root
        
    #     for a in a_list: 
    #        # child = self.get_children(current_node, a) # we can optimize this by using a dictionary instead of the linear search 
    #         if a in current_node.children: # in this case the current node has child already computed, we do not need to do intersection 
    #             #continue tree traversal 
    #             current_node = current_node.children[a] 
                
    #         else:
    #             #create a new node 
    #             new_node = Node(a)
    #             new_node.v_list = self.InvInd[a].intersection(current_node.v_list) 
    #             current_node.children[a] =  new_node 
    #             #self.nodes.add(new_node)
    #             #continue tree traversal 
    #             current_node = new_node 
                
    #     # update new rows 
    #     for row in current_node.v_list: 
    #         self.trie_new_rows[row].append(r_id)

    def ProcessRecord(self, r_id: int, a_set: set, ordering: list) -> set:
        """
        构建字典树（Trie）的核心逻辑，同时返回当前规则 (sample) 影响的行 ID 集合。
        
        Args:
            r_id (int): 当前规则 (sample) 的 ID。
            a_set (set): 当前规则的属性集合。
            ordering (list): 属性的预排序顺序，用于优化 Trie 的构建。

        Returns:
            set: 受当前规则影响的行 ID 集合。
        """
        # 将输入集合按照预排序顺序排序
        a_list = [x for x in ordering if x in a_set]

        # 遍历属性列表并更新字典树
        current_node = self._root

        for a in a_list:
            if a in current_node.children:
                # 如果当前节点已有该子节点，则继续遍历
                current_node = current_node.children[a]
            else:
                # 如果没有子节点，则创建一个新节点
                new_node = Node(a)
                # 更新新节点的有效行列表（通过交集计算）
                new_node.v_list = self.InvInd[a].intersection(current_node.v_list)
                current_node.children[a] = new_node
                current_node = new_node

        # 更新 trie_new_rows，并收集当前规则影响的行 ID
        affected_rows = set()
        for row in current_node.v_list:
            self.trie_new_rows[row].append(r_id)
            affected_rows.add(row)  # 收集受影响的行 ID

        return affected_rows