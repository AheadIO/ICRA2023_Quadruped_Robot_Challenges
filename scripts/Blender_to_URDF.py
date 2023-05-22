#!/usr/bin/env python
import rospy
import rospkg
import tf
import time
import os 
import csv

ros_root = rospkg.get_ros_root()
r = rospkg.RosPack()
PKG_NAME = "ICRA2023_Quadruped_Competition"
PKG_PATH = r.get_path(PKG_NAME)

class Obstacle():
    def __init__(self, name, id, size, pos, quat, euler) -> None:
        self.name = name
        self.id = id
        self.size = size
        self.pos = pos
        self.quat = quat
        self.euler = euler


class MapURDFGenerator:

    def __init__(self, name, path, macros):
        # init parameters
        self.package_path = path
        self.name = name
        self.file_path = self.package_path +'/urdf/map.urdf.xacro'
        self.macros = macros


    def generate(self, object_data):
        '''
        Make file in specific directory
        '''
        result = True
        # open file
        f = open(self.file_path, 'w+')

        # header
        f.write('<?xml version="1.0" ?>\n')
        f.write('<robot xmlns:xacro="http://ros.org/wiki/xacro" name="'+self.name+'">\n\n')
        f.write('\t<link name="world"/>\n\n')

        # include
        for macro in self.macros:
            f.write('\t<!-- ' + macro + ' -->\n')
            f.write('\t<xacro:include filename="$(find '+ PKG_NAME + ')/urdf/obstacles/' + macro + '.urdf.xacro"/>\n\n')

        # contents
        for obj in object_data:
            if obj.name != '':
                self.add_object(f, obj)

        # close
        f.write('\n\t<gazebo>\n')
        f.write('\t\t<static>true</static>\n')
        f.write('\t</gazebo>\n\n')

        f.write("</robot>")
        f.close()
        return True

    def add_object(self, file, obstacle):
        obj_name = obstacle.name

        position = str(obstacle.pos[0]) + ' ' + str(obstacle.pos[1]) + ' ' + str(obstacle.pos[2])

        quaternioin = obstacle.quat
        # convert quaternion to rpy
        # TODO: fix orientation problem in blender
        rpy = [0,0,0] #self.quaternion_to_euler(quaternioin)
        orientation = str(rpy[0]) + ' ' + str(rpy[1]) + ' ' + str(rpy[2])

        file.write('\t<xacro:obs_' + obj_name.replace("'", "inch") + ' parent="world" handle="' + str(obstacle.id) + '" position="' + position + '" orientation="' + orientation + '"/>\n')

    def quaternion_to_euler(self, quaternion):
        euler = tf.transformations.euler_from_quaternion(quaternion)
        roll = euler[0]
        pitch = euler[1]
        yaw = euler[2]
        return [roll, pitch, yaw]

class ObstacleURDFGenerator:

    def __init__(self, name, path, format):
        # init parameters
        self.package_path = path
        self.name = name
        self.format = format
        self.file_path = self.package_path +'/urdf/obstacles/' + self.name + '.urdf.xacro'


    def generate(self):
        '''
        Make file in specific directory
        '''
        result = True
        # open file
        f = open(self.file_path, 'w+')

        # header
        f.write('<?xml version="1.0" encoding="utf-8"?>\n\n')
        f.write('<robot xmlns:xacro="http://ros.org/wiki/xacro">\n')
        f.write('\t<xacro:macro name="obs_' + self.name.replace("'", "inch") + '" params="handle parent position orientation">\n\n')

        # virtual joint
        f.write('\t<joint name="' + self.name + '${handle}_joint" type="fixed">\n')
        f.write('\t\t<origin xyz="${position}" rpy="${orientation}"/>\n')
        f.write('\t\t<parent link="${parent}"/>\n')
        f.write('\t\t<child link="' + self.name + '${handle}"/>\n')
        f.write('\t</joint>\n\n')

        # link
        f.write('\t<link name="' + self.name + '${handle}">\n\n')

        f.write('\t\t<inertial>\n')
        f.write('\t\t\t<origin xyz="0 0 0" rpy="0 0 0"/>\n')
        f.write('\t\t\t<mass value="1"/>\n')
        f.write('\t\t\t<inertia\n')
        f.write('\t\t\t\tixx="1.0" ixy="0.0" ixz="0.0"\n')
        f.write('\t\t\t\tiyy="1.0" iyz="0.0"\n')
        f.write('\t\t\t\tizz="1.0"/>\n')
        f.write('\t\t</inertial>\n\n')

        f.write('\t\t<visual>\n')
        f.write('\t\t\t<origin xyz="0 0 0" rpy="0 0 0"/>\n')
        f.write('\t\t\t<geometry>\n')
        f.write('\t\t\t\t<mesh filename="package://ICRA2023_Quadruped_Competition/meshes/assembly/' + self.name + '.' + self.format + '"/>\n')
        f.write('\t\t\t</geometry>\n')
        f.write('\t\t\t<material name="">\n')
        f.write('\t\t\t</material>\n')
        f.write('\t\t</visual>\n\n')

        f.write('\t\t<collision>\n')
        f.write('\t\t\t<origin xyz="0 0 0" rpy="0 0 0"/>\n')
        f.write('\t\t\t<geometry>\n')
        f.write('\t\t\t\t<mesh filename="package://ICRA2023_Quadruped_Competition/meshes/assembly/' + self.name + '.' + self.format + '"/>\n')
        f.write('\t\t\t</geometry>\n')
        f.write('\t\t\t<material name="">\n')
        f.write('\t\t\t</material>\n')
        f.write('\t\t</collision>\n\n')

        f.write('\t</link>\n\n')


        f.write('\t<gazebo reference="'+ self.name + '${handle}">\n')
        f.write('\t</gazebo>\n\n')

        # close
        f.write("\t</xacro:macro>\n")
        f.write("</robot>")
        f.close()
        return True


object_instances = []
object_ids = []
object_cnt = {}
['1200x2400_OSB', '1200x600_OSB', '12_00x1200_OSB_1', '12_00x1200_OSB', '1_1m_5x10cm_beam', '1_2m_5x10cm_beam_1', '1_2m_5x10cm_beam', '1', '2_4m_5x10cm_beam', '2', '300x600_OSB', '3', "42'_2x2_baluster", '450mm_hurdle_retainer', '4_1', '5x5x30_cm_wall_corner', '600x1200_OSB', '600x2400_OSB', '', 'Component_246', 'Component_247', 'Component_248', 'Component_249', 'Component_251', 'Component_272', 'Component_2', 'Component_363', 'Component_7', 'Crate_4', 'Diagonal_beam_5x10cm_1', 'fin_2', 'foam', 'Group_1595', 'Group_1596', 'Group_2258', 'Group_2261', 'Group_362', 'Group_368', 'Group_369', 'Group_36', 'Group_371', 'Group_38', 'Group_41', 'Group_73', 'Group_74', 'Group_75', 'Group_9', 'Half_Crate', 'Hingeplate', 'Hurdle_pipe', 'Hurdle_spacer', 'K_rail_rail', 'Obstructed1', 'Obstructed1A', 'Obstructed2', 'Obstructed2A', 'Obstructed3', 'Obstructed3A', 'Obstructed4', 'Obstructed4A', 'Pallet_leg', 'Ramp_side', 'Ramp_top', 'RampBrace', 'Slope_back', 'Slope_backplate', 'Slope_leg', 'Slope_post_1', 'Slope_post_2', 'Slope_sidewall', 'Sloper_brace', 'WtBkt_GrnRng_8in_4', 'WtBkt_GrnRng_8in_5']  #73

# read csv file line by line by ;
with open(PKG_PATH + '/scripts/object_list.txt','r') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=';')
    for i, row in enumerate(csvreader):
        alias = row[0].split('.')
        id = 0

        name = alias[0] # alias[0].split('__')[0]
        if name in object_cnt:
            object_cnt[name] += 1
            id = object_cnt[name]
        else:
            object_cnt[name] = 0

        size = [float(row[1]), float(row[2]), float(row[3])]
        pos = [float(row[4]), float(row[5]), float(row[6])]
        quat = [float(row[7]), float(row[8]), float(row[9]), float(row[10])]
        euler = [float(row[11]), float(row[12]), float(row[13])]
        object_instances.append(Obstacle(name, id, size, pos, quat, euler))
        object_ids.append(name)

# remove duplicate name in list
object_ids = list(dict.fromkeys(object_ids))
print((object_ids, len(object_ids)))

for obj in object_instances:
        ug = ObstacleURDFGenerator(obj.name, PKG_PATH, 'obj')
        ug.generate()

ug = MapURDFGenerator('competition_map', PKG_PATH, object_ids)
ug.generate(object_instances)

