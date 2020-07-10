import datetime
# 该文件是最新的C3D6的内聚力插入文件，配合多晶生成插件，可以完成插入
# 更加不易出错（对于inp文件格式的依赖降低）
# 作者：杨晟泽    时间：2020.4.24
# 完全适用于用于形成北极星一个多晶切削教程，多晶建模可以联系 QQ 1922875732
# 全局变量
name = ''
for i in range(24):     # range后面的数字是set集合的数目（不包括总的集合）
    add_str = "GrainGroup-{};".format(i+1)      # set的前缀
    name += add_str
# 上面变量写出set的名称，例:"Set-1;Set-2" 文件中所有generate格式的element的set
set_list = name[:-1].split(';')       # set列表
file_name = 'test1.inp'          # 要插入的文件名（生成的文件为result.inp） 重要！
text = []                       # 读取文件的信息列表
set_message = []                # 初始文件中的set信息
node_dict = {}                  # 初始的节点列表
node_len = 0                    # 初始的节点列表的长度
element_dict = {}               # 单元列表（期间会经历一次修改get_message()和modify_data()下面分别print试一试）
element_len = 0                 # 初始单元列表的长度
node_appearance = {}            # 每个节点分裂的次数
new_node = {}                   # 新的节点（分裂后）的列表
cohesive_dict = {}              # 生成的内聚单元的列表
k = 0                           # 计数符号K，与生成内聚单元有关
edge_dict = {}                  # 晶界处的内聚单元列表
inter_dict = {}                 # 晶粒处的内聚单元列表


# 获取inp文件中的所有节点、单元的信息
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
        elif i.startswith('*Elset') or i.startswith('*End') or i.startswith('*Nset'): break
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


# 获取一个节点需要分裂的次数（或者可以理解为一个节点周围有几个单元，分裂次数 = 单元数量[具体实现函数见modify_data]）
def get_node_appear(element_dict, node_dict):
    global node_appearance
    node_appearance = dict.fromkeys(node_dict, 0)
    for i in element_dict:
        for j in element_dict[i]:
            node_appearance[j] += 1
    return node_appearance


# 寻找分裂后的节点的源节点
def fin_source_node(x):
    # max_node = len(node_dict)     # 程序过程优化
    max_node = node_len
    dele_len = len(str(max_node))
    if len(x) <= dele_len:
        return x
    if len(x) > dele_len:
        return str(int(x[-dele_len:]))


# 获取一个set里的所有的单元（和旧的c3d6_insert脚本有所不同）
def get_set_element(setname):
    value = False
    generate_value = False
    set_element_dict = {}
    for i in text:
        if i == '*Elset, elset={}, generate\n'.format(setname):
            generate_value = True
        if i == '*Elset, elset={}\n'.format(setname):
            value = True
        if i.startswith('*Nset') or i.startswith('*End Part'):
            value = False
            generate_value = False
        if value and i != '*Elset, elset={}\n'.format(setname):
            T = i.replace(' ', '').replace('\n', '').split(',')
            while '' in T:
                T.remove('')
            for i in T:
                set_element_dict[i] = element_dict[i]
        if generate_value and i != '*Elset, elset={}, generate\n'.format(setname):
            T = i.replace(' ', '').replace('\n', '').split(',')
            for i in range(int(T[0]),int(T[1])+1):
                set_element_dict[str(i)] = element_dict[str(i)]
    return set_element_dict


# 获取两个set单元集合里的节点的交集
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


# 获取所有的晶粒(set)之间的交点，并生成列表，如[ [set-1,set-2,[1,2,3,4]],[set-1],set-3,[4,6,7,5],.... ]
def get_all_intersection(set_list1):
    all = []
    re_all = []
    for i in range(len(set_list1)):
        for j in range(i+1,len(set_list1)):
            a = intersection(get_set_element(set_list[i]),get_set_element(set_list[j]))
            s = [set_list1[i],set_list1[j],a]
            all.append(s)
    for i in all:
        if i[2].__len__() == 0:
            pass
        else:
            re_all.append(i)
    return re_all


# 将节点重新划分，并修正单元
def modify_data():
    global new_node
    global node_appearance
    get_node_appear(element_dict,node_dict)
    max_node = len(node_dict)
    for i in node_dict:
        for j in range(node_appearance[i]):
            new_node[str(j * 10**len(str(max_node)) + int(i))] = node_dict[i]
    Node_assign = dict.fromkeys(node_dict, 0)
    for i in element_dict:
        for j in range(6):
            if Node_assign[element_dict[i][j]] < node_appearance[element_dict[i][j]]:
                Newnode = str(Node_assign[element_dict[i][j]] * (10 ** (len(str(max_node)))) + int(element_dict[i][j]))
                element_dict[i][j] = Newnode
                Node_assign[fin_source_node(element_dict[i][j])] += 1


# 获取所有的存在的内聚力单元
def get_cohesive_all():
    global cohesive_dict
    global k
    # for i in element_dict:
    #     k = int(i)
    k = element_len + 1
    # element_sort = sorted(int(i) for i in element_dict)
    # for i in element_sort:
    #     for j in range(i+1,element_len+1):
    #         l = []
    #         for m in element_dict[str(i)]:
    #             for n in element_dict[str(j)]:
    #                 if fin_source_node(m) == fin_source_node(n):
    #                     l.append([m,n])
    #         if len(l) == 4:
    #             cohesive_dict[str(k)] = [l[0][0],l[1][0],l[3][0],l[2][0],l[0][1],l[1][1],l[3][1],l[2][1]]
    #             k += 1
    # 以上程序是正确的，但是四重循环的算法复杂度过高，过于耗时,可以试运行一下test4和test5.
    # 这里用三重循环来代替，除去部分不必要的运算，略为减少运算时间.
    for i in element_dict:
        for j in range(int(i)+1,element_len+1):
            l = []
            k1 = []
            k2 = []
            l1 = []
            for m in element_dict[i]:
                l.append(m)
            for n in element_dict[str(j)]:
                l.append(n)
            for s in l:
                k1.append(fin_source_node(s))
                k2 = sorted(set(k1), key=k1.index)
            if len(k2) == 8:
                for j in l:
                    for r in l:
                        if j != r and fin_source_node(j) == fin_source_node(r):
                            l1.append([j,r])
            try:
                cohesive_dict[str(k)] = [l1[0][0], l1[1][0], l1[3][0], l1[2][0], l1[0][1], l1[1][1], l1[3][1],l1[2][1]]
            except:
                pass
            k += 1
    # 该实现方式可以减少约一半时间，当单元数量为8000时，旧方法需要40分钟，新方法需要20分钟.
    # 如发现更好的算法，欢迎联系我


# 从总的内聚单元中筛选晶界/晶粒的内聚单元
def identify_interface():
    global edge_dict
    global inter_dict
    for i in node_l:
        for j in cohesive_dict:
            s = 0
            for m in cohesive_dict[j]:
                if fin_source_node(m) in i[2]:
                    s += 1
                else: pass
                if s == 8:
                    edge_dict[j] = cohesive_dict[j]
    for i in cohesive_dict:
        if i in edge_dict:
            pass
        else:
            inter_dict[i] = cohesive_dict[i]

# 这里运行功能函数，并计算每个函数的总耗时
starttime = datetime.datetime.now()
get_message()
endtime = datetime.datetime.now()
print('get_message耗时(s):',(endtime-starttime).seconds)
starttime = datetime.datetime.now()
node_l = get_all_intersection(set_list)
endtime = datetime.datetime.now()
print('get_all_intersection耗时(s):',(endtime-starttime).seconds)
starttime = datetime.datetime.now()
modify_data()
endtime = datetime.datetime.now()
print('modify_data耗时(s):',(endtime-starttime).seconds)
starttime = datetime.datetime.now()
get_cohesive_all()
endtime = datetime.datetime.now()
print('get_cohesive_all耗时(s):',(endtime-starttime).seconds)
starttime = datetime.datetime.now()
identify_interface()
endtime = datetime.datetime.now()
print('identify_interface耗时(s):',(endtime-starttime).seconds)
starttime = datetime.datetime.now()
# 书写数据
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
for i in set_list:
    file.write('*Elset, elset={}\n'.format(i))
    a = get_set_element(i)
    for j in a:
        file.write(j+'\n')
file.write('*Elset, elset=Cohesive-all-set, generate\n')
file.write('{0},   {1},   1'.format(element_len+1,k-1))
file.write('\n')
file.write('*Elset, elset=Cohesive-inter-set\n')
inter_sort = sorted([int(i) for i in inter_dict.keys()])
for i in inter_sort:
    file.write(str(i))
    file.write(', \n')
file.write('*Elset, elset=Cohesive-interface-set\n')
interfance_sort = sorted([int(i) for i in edge_dict.keys()])
for i in interfance_sort:
    file.write(str(i))
    file.write(',   \n')
file.write('*End Part')

endtime = datetime.datetime.now()
print('书写文件耗时(s):',(endtime-starttime).seconds)
print('成功插入，请用abaqus打开result.inp文件检查嵌入结果')
