# -*- coding: mbcs -*-
# -- coding: utf-8 --
import csv
from textRepr import *
from odbAccess import *
import os
import numpy as np

class Output_from_ODB():
    
    """
    only one instance for an object
    """

    def __init__(self, jobname, tpath = os.getcwd()):
        self.odb = jobname+".odb"
        self.tpath = tpath#task path
        self.oPath=os.path.join(self.tpath,self.odb) #odb path
        self.o = session.openOdb(name=self.oPath,readOnly=True)#read only prevent nodeset from being written into odb
        self.Current_Output = {}


    def path(self, number,instance = "GC-1"):

        """
        number is a dictionary. The key is the name of the path.
        The value includes the start, end point and the amount of points.
        """

        inst1 = self.o.rootAssembly.instances[instance]
        self.full_number = {}
        self.nodeset = {}
        for name,number in number.items():
            self.full_number[name] = map(int,np.linspace(number[0],number[1],number[2],endpoint=True))
            self.nodeset[name] = inst1.NodeSetFromNodeLabels(name = name, nodeLabels = self.full_number[name])


    def Coordinate_Along_Path(self,steps,frame):
        def generator(values,i):
            for value in values:
                yield value.data[i]
        
        frames = self.o.steps[steps].frames
        f1 = frames[frame]
        fop = f1.fieldOutputs
        COO = fop["COORD"]
        for name, nodeset in self.nodeset.items():
            self.Current_Output[name] = self.full_number[name]
            self.Current_Output[name+"x"] = np.array([item for item in generator(COO.getSubset(region = nodeset).values,0)])
            self.Current_Output[name+"y"] = np.array([item for item in generator(COO.getSubset(region = nodeset).values,1)])
            self.Current_Output[name+"z"] = np.array([item for item in generator(COO.getSubset(region = nodeset).values,2)])
        return self.Current_Output


    def thickness(self, group):
        for groupname, group in group.items():
            self.Current_Output[groupname+"thickness"] =\
                  np.array(((self.Current_Output[group[0]+"x"]-self.Current_Output[group[1]+"x"])**2+
                  (self.Current_Output[group[0]+"y"]-self.Current_Output[group[1]+"y"])**2+
                  (self.Current_Output[group[0]+"z"]-self.Current_Output[group[1]+"z"])**2)**0.5)
        return self.Current_Output


    def height_of_tube(self, pathname, threshold,originalheight):
        A = np.zeros(len(self.Current_Output[pathname]))
        A[self.Current_Output[pathname+"x"]<threshold] = 1
        count = sum(A)
        self.Current_Output["height"] = [(self.Current_Output[pathname+"z"][count]+(self.Current_Output[pathname+"z"][count+1]-self.Current_Output[pathname+"z"][count])*(182-self.Current_Output[pathname+"x"][count])/(self.Current_Output[pathname+"x"][count+1]-self.Current_Output[pathname+"x"][count]))-originalheight]
        return self.Current_Output
        
        
    def minimum_thickness(self,group):
        for groupname, group in group.items():
            minimum = self.Current_Output[groupname+"thickness"][0]
            for thickness,x in zip(self.Current_Output[groupname+"thickness"],self.Current_Output[group[1]+'x']):
                if x>182:
                    continue
                if minimum > thickness:
                    minimum = thickness
            self.Current_Output[groupname+"thickness"] = [minimum]
        return self.Current_Output
        
        
    def write_CSV(self,csvname):
        def generator2(dict):
            length = 0
            
            for key,value in dict.items():
                if type(value) is np.ndarray or type(value) is np.array:
                    dict[key] = value.tolist()
                if len(value) > length:
                    length = len(value)
            for key in dict.keys():
                dict[key] = dict[key]+([None] * (length-len(dict[key])))
            for i in range(length):
                dict_split = {}
                for key in dict.keys():
                    dict_split[key] = dict[key][i]
                yield dict_split
                                       
        csvpath = csvname+".csv"
        if os.path.exists(csvpath):
            os.remove(csvpath)
        with open(csvpath, "wb") as csvfile:
            fieldnames = sorted(self.Current_Output)
            writer = csv.DictWriter(csvfile,fieldnames = fieldnames)
            writer.writeheader()
            writer.writerows(generator2(self.Current_Output))
            
    def eliminate_output(self):
        self.Current_Output = {}
        
            
            
##########################################################################################################
jobname1 = ["0","elastic2","fluid-55Mpa"]
#jobname2 = ["no1","no2","no3","no4","no5","no6","no7","no8","no9","no10","no11"]
jobname2 = ["no1","no2","no3","no4","no5","no6","no7","no8","no10","no11"]
number = {"AO":[53381,54161,157],\
        "AI":[53385,54165,157],\
        "BO":[1,781,157],\
        "BI":[5,785,157],\
        "CO":[781,54161,69],\
        "CI":[785,54165,69],\
        "ALLI":[1,54161,10833],\
        "ALLO":[5,54165,10833]}
group1 = {"A":["AI","AO"],\
        "B":["BI","BO"],\
        "C":["CI","CO"],\
        "ALL":["ALLI","ALLO"]}
group2 = {"ALL":["ALLI","ALLO"]}

def output(jobname,instance ,number,steps,frame,group1,group2,pathname,threshold,originalheight):
    try:
        publication = Output_from_ODB(jobname = jobname)
        publication.path(instance = instance, number = number)
        publication.Coordinate_Along_Path(steps = steps,frame = frame)
        publication.thickness(group = group1)
        publication.height_of_tube(pathname = pathname,threshold = threshold,originalheight=originalheight)
        publication.minimum_thickness(group = group2)
        publication.write_CSV(jobname+' '+str(frame))
    finally:
        publication.o.close()#no matter bug or not, if dont close odb, the name of nodeset will be engaged forever

output("fluid-55Mpa","GC-1",number,"Step-1",20,group1,group2,"AO",182,114)  
output("0","GC-1",number,"Step-1",6,group1,group2,"AO",182,114) 
output("0","GC-1",number,"Step-1",8,group1,group2,"AO",182,114) 
output("0","GC-1",number,"Step-1",12,group1,group2,"AO",182,114) 
output("elastic2","GC-1",number,"Step-1",14,group1,group2,"AO",182,114) 
#for jobname in jobname1:
#    output(jobname,"GC-1",number,"Step-1",14,group1,group2,"AO",182,114)
for jobname in jobname2:
    output(jobname,"GC-1",number,"Step-2",20,group1,group2,"AO",182,114)