# 2d批量插入cohesive单元
# 该插件不支持neper生成的文件格式（需要小小修改一下inp文件)，正常abaqus生成的文件可以使用
# 作者： ShengZe Yang.
import re

# 全局变量
name = 'f1;f2;f3;f4;f5;f6;f7;f8;f9;f10;f11;f12;f13;f14;f15;f16;f17;f18;f19;f20'
# 上面变量写出set的名称，例:"Set-1;Set-2" 文件中所有generate格式的element的set
set_list = name.split(';')
file_name = "test4.inp"     # 文件名[按照自己需求修改]
node_len = 0                # 最初文件中，节点总个数
element_len = 0             # 最初文件中，单元总个数
text = []                   # 遍历后的每一行的列表
node_dict = {}              # 所有节点的集合
element_dict = {}           # 所有内聚单元的集合
node_appearance = {}        # 每个节点出现的次数(划分前)
new_node = {}               # 划分后的节点集合
cohesive_dict = {}          # 总的内聚单元集合
k = 0                       # 计数单位
edge_dict = {}              # 晶界的内聚单元集合
inter_dict = {}             # 晶粒的内聚单元集合
node_l = []                 # 携带晶界上的Node及晶界两边的Set信息的列表
set_message = []            # 携带原文件上每个set包含的element信息的列表

# 该函数遍历文件，获取点和单元的长度、集合。
def get_message(file_name):
    global node_dict
    global element_dict
    ori_inp = open(file_name)
    global text
    text = ori_inp.readlines()
    # node
    eigenvalue = False
    for i in text:
        if i.startswith('*Node'):
            eigenvalue = True
        elif i.startswith('*Element'):
            break
        else: pass
        if eigenvalue and i != '*Node\n':
            T = i.replace(' ', '').replace('\n', '').split(',')
            node_dict[T[0]] = T[1:]
        else: pass
    # element
    eigenvalue = False
    for i in text:
        if i.startswith('*Element'):
            eigenvalue = True
        elif i.startswith('*Nset') or i.startswith('*End'):
            break
        else: pass
        if eigenvalue:
            if i.startswith('*Element'): pass
            else:
                T = i.replace(' ', '').replace('\n', '').split(',')
                element_dict[T[0]] = T[1:]
        else: pass
    global node_len
    node_len = len(node_dict)
    global element_len
    element_len = len(element_dict)
    ori_inp.close()


# 中间函数：该函数用来获取指定Set的所有Element集合，并生成dict
def get_set_element(set):
    def get_set_extreme(set):
        for i in range(len(text)):
            if text[i].startswith('*Elset, elset={}'.format(set)):
                start = int(text[i + 1].replace(' ', '').replace('\n', '').split(',')[0])
                end = int(text[i + 1].replace(' ', '').replace('\n', '').split(',')[1])
                return [start, end]
            else: pass
    eigenvalue = False
    set_element_dict = {}
    start = get_set_extreme(set)[0]
    end = get_set_extreme(set)[1]
    for i in text:
        if i.startswith('*Element'):
            eigenvalue = True
        elif i.startswith('*Nset'):
            return set_element_dict
        else: pass
        if eigenvalue:
            if i.startswith('*Element'): pass
            else:
                T = i.replace(' ', '').replace('\n', '').split(',')
                if int(T[0]) in range(start,end+1):
                    set_element_dict[T[0]] = T[1:]
        else: pass


# 中间函数：获取两个Set的节点的交集
def intersection(set1,set2):
    def list_insert(set_,list_):
        for i in set_:
            for j in set_[i]:
                if j not in list_:
                    list_.append(j)
    n1 = []
    n2 = []
    list_insert(set1,n1)
    list_insert(set2,n2)
    return [var for var in n1 if var in n2]


# 该函数用来生成列表内所有的Set的相邻点，并生成列表
def get_all_intersection(set_list):
    all = []
    re_all = []
    for i in range(len(set_list)):
        for j in range(i+1,len(set_list)):
            a = intersection(get_set_element(set_list[i]),get_set_element(set_list[j]))
            s = [set_list[i],set_list[j],a]
            all.append(s)
    for i in all:
        if i[2].__len__() == 0:
            pass
        else:
            re_all.append(i)
    return re_all


# 寻找源节点（如1001节点的源节点是1，同理1023->23 .etc）
def fin_source_node(x):
    max_node = len(node_dict)
    dele_len = len(str(max_node))
    if len(x) <= dele_len:
        return x
    if len(x) > dele_len:
        return str(int(x[-dele_len:]))


# 将节点重新划分，并修正单元
def modify_data():
    def get_node_appear(element_dict, node_dict):
        global node_appearance
        node_appearance = dict.fromkeys(node_dict, 0)
        for i in element_dict:
            for j in element_dict[i]:
                node_appearance[j] += 1
        return node_appearance
    global new_node
    global node_appearance
    get_node_appear(element_dict,node_dict)
    # node_appearance = get_node_appear(element_dict,node_dict)
    max_node = len(node_dict)
    for i in node_dict:
        for j in range(node_appearance[i]):
            new_node[str(j * 10**len(str(max_node)) + int(i))] = node_dict[i]

    # node_str_len = len(str(max_node))
    # n_node_app = dict.fromkeys(new_node, 1)
    # 下面这个方法是旧方法，在单元为三棱柱情况下会出重大bug
    # for i in element_dict:
    #     for j in range(3):
    #         for k in n_node_app:
    #             if n_node_app[k] != 0 and fin_source_node(k) == element_dict[i][j]:
    #                 element_dict[i][j] =k
    #                 n_node_app[k] = 0
    Node_assign = dict.fromkeys(node_dict, 0)
    for i in element_dict:
        for j in range(3):
            if Node_assign[element_dict[i][j]] < node_appearance[element_dict[i][j]]:
                Newnode = str(Node_assign[element_dict[i][j]] * (10 ** (len(str(max_node)))) + int(element_dict[i][j]))
                element_dict[i][j] = Newnode
                Node_assign[fin_source_node(element_dict[i][j])] += 1


# 生成总的内聚单元
def get_cohesive_all():
    global cohesive_dict
    global k
    k = element_len + 1
    element_sort = sorted(int(i) for i in element_dict)
    for i in element_sort:
        for j in range(i+1,element_len+1):
            l = []
            for m in element_dict[str(i)]:
                for n in element_dict[str(j)]:
                    if fin_source_node(m) == fin_source_node(n):
                        l.append([m,n])
            if len(l) == 2:
                cohesive_dict[str(k)] = [l[1][0],l[0][0],l[0][1],l[1][1]]
                k += 1


# 从总的内聚单元中筛选晶界的内聚单元
def identify_interface(set_list):
    global node_l
    node_l = get_all_intersection(set_list)
    all_inter_node = []
    global edge_dict
    global inter_dict
    # for i in node_l:
    #     for j in i[2]:
    #         if j not in all_inter_node:
    #             all_inter_node.append(j)
    # for i in cohesive_dict:               # 该串代码会造成BUG
    #     s = 0
    #     for j in cohesive_dict[i]:
    #         if fin_source_node(j) in all_inter_node:
    #             s += 1
    #         else: pass
    #         if s == 4:
    #             edge_dict[i] = cohesive_dict[i]
    for i in node_l:
        for j in cohesive_dict:
            s = 0
            for m in cohesive_dict[j]:
                if fin_source_node(m) in i[2]:
                    s += 1
                else: pass
                if s == 4:
                    edge_dict[j] = cohesive_dict[j]


# 提取晶粒内的内聚单元
def identify_inter():
    for i in cohesive_dict:
        if i in edge_dict:
            pass
        else:
            inter_dict[i] = cohesive_dict[i]

# 获取原始的inp文件中的set的element信息
def get_set_message():
    global set_message
    set_message = []
    for i in range(len(text)):
        if text[i].startswith('*Elset, elset='):
            set_name = re.findall(r'Elset, elset=(.*?),',text[i])
            set_node = text[i+1]
            set_message.append([set_name[0],set_node])

# 测试部分（如无需要可以把所有print注释）
get_message(file_name)

print("节点总个数:",node_len)
print('单元总个数:',element_len)
print('初始节点集合：',node_dict)
print('初始单元集合：',element_dict)
get_set_message()
modify_data()

print('每个节点出现次数：',node_appearance)
print('修正后的节点集合:',new_node)
print('修正后的单元集合:',element_dict)

get_cohesive_all()

print('全局内聚单元:',cohesive_dict)
print('计数单位K：',k)

identify_interface(set_list)
identify_inter()

print('晶界处的内聚单元：',edge_dict)
print(len(edge_dict))
print('晶粒内的内聚单元',inter_dict)

interfance_sort = sorted([int(i) for i in edge_dict.keys()])
print(interfance_sort)
print(len(interfance_sort))

# 实施文件书写
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
    file.write('\n')

file.write('*Element, type=CPS3\n')
n_element_sort = sorted([int(i) for i in element_dict.keys()])
for i in n_element_sort:
    file.write(str(i))
    file.write(',    ')
    file.write(element_dict[str(i)][0])
    file.write(',    ')
    file.write(element_dict[str(i)][1])
    file.write(',    ')
    file.write(element_dict[str(i)][2])
    file.write('\n')

file.write('*Element,type=COH2D4\n')
cohesive_sort = sorted([int(i) for i in cohesive_dict.keys()])
print(cohesive_sort)
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
    file.write('\n')

file.write('*Elset, elset=Elset-union, generate\n')
file.write('1,   {},   1\n'.format(element_len))
for i in set_message:
    file.write('*Elset, elset={}, generate\n'.format(i[0]))
    file.write(i[1])
file.write('*Elset, elset=Cohesive-all-set, generate\n')
file.write('{0},   {1},   1'.format(element_len+1,k-1))
file.write('\n')
file.write('*Elset, elset=Cohesive-inter-set\n')
inter_sort = sorted([int(i) for i in inter_dict.keys()])
for i in inter_sort:
    file.write(str(i))
    file.write(',   \n')
file.write('*Elset, elset=Cohesive-interface-set\n')
interfance_sort = sorted([int(i) for i in edge_dict.keys()])
print(interfance_sort)
print(len(interfance_sort))
for i in interfance_sort:
    file.write(str(i))
    file.write(',   \n')
file.write('*End Part')
