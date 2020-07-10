# 该脚本只适用于YSZ个人，请勿直接套用，以免报错
# 该脚本只支持单层的三棱柱单元的插入，多层的会报错（我的实验只用到单层，所以多层的不出意外我不会开发）
# 网格只支持c3d6网格
# 该脚本已经过于老旧，请参考New_c3d6_insert  2020.4.25
# 全局变量
file_name = 'test.inp'
text = []
node_dict = {}
node_len = 0
element_dict = {}
element_len = 0
node_appearance = {}
new_node = {}
cohesive_dict = {}
k = 0
n_node_app = {}


# 获取文件信息，如节点、单元个数和字典
def get_message():
    global node_dict
    global node_len
    global text
    ori_inp = open(file_name)
    text = ori_inp.readlines()
    # node
    value = False
    for i in text:
        if i.startswith('*Node'):
            value = True
        elif i.startswith('*Element'): break
        if value and i != '*Node\n':
            T = i.replace(' ','').replace('\n','').split(',')
            node_dict[T[0]] = T[1:]
        else: pass
    try: del node_dict['']
    except: pass
    node_len = len(node_dict)
    global element_dict
    global element_len
    # Element
    eigenvalue = False
    for i in text:
        if i.startswith('*Element'):
            eigenvalue = True
        elif i.startswith('*Elset') or i.startswith('*End'): break
        else: pass
        if eigenvalue:
            if i.startswith('*Element'): pass
            else:
                T = i.replace(' ', '').replace('\n', '').split(',')
                element_dict[T[0]] = T[1:]
        else: pass
    try: del element_dict['']
    except: pass
    element_len = len(element_dict)


def fin_source_node(x):
    max_node = len(node_dict)
    dele_len = len(str(max_node))
    if len(x) <= dele_len:
        return x
    if len(x) > dele_len:
        return str(int(x[-dele_len:]))


def get_node_appear(element_dict, node_dict):
    global node_appearance
    node_appearance = dict.fromkeys(node_dict, 0)
    for i in element_dict:
        for j in element_dict[i]:
            node_appearance[j] += 1
    return node_appearance


# 将节点重新划分，并修正单元
def modify_data():
    global new_node
    global node_appearance
    get_node_appear(element_dict,node_dict)
    max_node = len(node_dict)
    print(max_node)
    for i in node_dict:
        for j in range(node_appearance[i]):
            new_node[str(j * 10**len(str(max_node)) + int(i))] = node_dict[i]

    # node_str_len = len(str(max_node))             # 该代码会出现BUG
    # print(node_str_len)
    # global n_node_app
    # n_node_app = dict.fromkeys(new_node, 1)
    # print(n_node_app)
    # for i in element_dict:
    #     #print('i:',i)
    #     for j in range(len(element_dict['1'])):
    #         #print('j:',j)
    #         for k in n_node_app:
    #             print('k:',k,'f_s',fin_source_node(k))
    #             if n_node_app[k] != 0 and fin_source_node(k) == fin_source_node(element_dict[i][j]):
    #                 print('element_dict[i][j]:',element_dict[i][j],',k:',k,',i:',i,',j:',j)
    #                 element_dict[i][j] = k
    #                 n_node_app[k] = 0
    Node_assign = dict.fromkeys(node_dict, 0)
    print(Node_assign)
    for i in element_dict:
        for j in range(6):
            if Node_assign[element_dict[i][j]] < node_appearance[element_dict[i][j]]:
                Newnode = str(Node_assign[element_dict[i][j]] * (10 ** (len(str(max_node)))) + int(element_dict[i][j]))
                element_dict[i][j] = Newnode
                Node_assign[fin_source_node(element_dict[i][j])] += 1
    print(Node_assign)
    print(element_dict)


def get_cohesive_all():
    global cohesive_dict
    global k
    k = element_len + 1
    element_sort = sorted(int(i) for i in element_dict)
    # print('element_sort:',element_sort)
    for i in element_sort:
        for j in range(i+1,element_len+1):
            l = []
            for m in element_dict[str(i)]:
                for n in element_dict[str(j)]:
                    if fin_source_node(m) == fin_source_node(n):
                        l.append([m,n])
            if len(l) == 4:
               # print(l)
                cohesive_dict[str(k)] = [l[0][0],l[1][0],l[3][0],l[2][0],l[0][1],l[1][1],l[3][1],l[2][1]]
                k += 1


get_message()
# print(node_dict)
print('单元',element_dict)
# print(node_len)
# print(element_len)
modify_data()
print('新节点',new_node)
print('近邻表',node_appearance)
# print('重整后的单元',element_dict)
get_cohesive_all()

# 开始书写文件
file = open('result.inp','w')
for i in range(len(text)):
    file.write(text[i])
    if text[i].startswith('*Node'):
        break
n_node_sort = sorted([int(i) for i in new_node.keys()])
for i in n_node_sort:
    file.write(str(i))
    file.write(',    ')
    file.write(new_node[str(i)][0])
    file.write(',    ')
    file.write(new_node[str(i)][1])
    file.write(',    ')
    file.write(new_node[str(i)][2])
    file.write('\n')

file.write('*Element, type=C3D6\n')
n_element_sort = sorted([int(i) for i in element_dict.keys()])
for i in n_element_sort:
    file.write(str(i))
    file.write(',    ')
    file.write(element_dict[str(i)][0])
    file.write(',    ')
    file.write(element_dict[str(i)][1])
    file.write(',    ')
    file.write(element_dict[str(i)][2])
    file.write(',    ')
    file.write(element_dict[str(i)][3])
    file.write(',    ')
    file.write(element_dict[str(i)][4])
    file.write(',    ')
    file.write(element_dict[str(i)][5])
    file.write('\n')

file.write('*Element, type=COH3D8\n')
cohesive_sort = sorted([int(i) for i in cohesive_dict.keys()])
for i in cohesive_sort:
    file.write(str(i))
    file.write(',    ')
    file.write(cohesive_dict[str(i)][0])
    file.write(',    ')
    file.write(cohesive_dict[str(i)][1])
    file.write(',    ')
    file.write(cohesive_dict[str(i)][2])
    file.write(',    ')
    file.write(cohesive_dict[str(i)][3])
    file.write(',    ')
    file.write(cohesive_dict[str(i)][4])
    file.write(',    ')
    file.write(cohesive_dict[str(i)][5])
    file.write(',    ')
    file.write(cohesive_dict[str(i)][6])
    file.write(',    ')
    file.write(cohesive_dict[str(i)][7])
    file.write('\n')
file.write('*Elset, elset=Elset-union, generate\n')
file.write('1,   {},   1\n'.format(element_len))
file.write('*Elset, elset=Cohesive-all-set, generate\n')
file.write('{0},   {1},   1'.format(element_len+1,k-1))
file.write('\n')
file.write('*End Part')

