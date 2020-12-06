import networkx as nx
from parse import read_input_file, write_output_file
from utils import is_valid_solution, calculate_happiness, calculate_happiness_for_room, calculate_stress_for_room, convert_dictionary
import sys
from os.path import basename, normpath
import glob


def solve(G, s):
    """
    Args:
        G: networkx.Graph
        s: stress_budget
    Returns:
        D: Dictionary mapping for student to breakout room r e.g. {0:2, 1:0, 2:1, 3:2}
        k: Number of breakout rooms
    """
    # we are originally starting k off as 1, we will continually add groups until we have a valid assignment
    num_groups = 1
    stress_limit = s / num_groups
    curr_room = 0

    room_to_student = {0: []}
    students_left = []

    # initially, all students are still left unmatched
    num_students = G.order()
    for i in range(num_students):
        students_left.append(i)

    while students_left:
        room = room_to_student[curr_room]
        if not room:
            # current room is empty
            best_pair = find_best_pair(G, students_left, stress_limit)
            if best_pair == -1:
                # there exist no pairs that satisfy the current stress limit, cannot form any more groups
                for student in students_left:
                    room_to_student[curr_room] = [student]
                    students_left.remove(student)
                    curr_room += 1
                num_groups = len(room_to_student)
                curr_room = num_groups - 1
            else:
                # there exists a best pair that satisfies the current stress limit
                students_left.remove(best_pair[0])
                students_left.remove(best_pair[1])
                room.append(best_pair[0])
                room.append(best_pair[1])
        else:
            # current room is not empty
            new_member = find_best_addition(G, students_left, stress_limit, room)
            if new_member == -1:
                # we cannot add anyone to the current group
                num_groups += 1
                stress_limit = s / num_groups
                curr_room += 1
                for i in range(len(room_to_student)):
                    trim_group(G, students_left, stress_limit, room_to_student[i])
                room_to_student[curr_room] = []
                
            else: 
                # we can add someone to the current group
                room.append(new_member)
                students_left.remove(new_member)

    return convert_dictionary(room_to_student), curr_room + 1, room_to_student


# Returns the pair of students i, j w/ the highest hij / sij value such that sij < stress_limit
# out of all the remaining students. If a pair cannot be found, returns -1
# 
# If a pair cannot be found, that means we cannot add any pair of students to a breakout room without
# breaking our stress limit. In this case, enumerate the rest of the groups into breakout rooms for the solution
#
# DOESNT CHANGE group OR students_left
def find_best_pair(G, students_left, stress_limit):
    max_ratio = 0
    max_pair = -1
    for x in range(len(students_left)):
        for y in range(x + 1, len(students_left)):
            # print(students_left[x], students_left[y])
            hij = G.get_edge_data(students_left[x], students_left[y])['happiness']
            sij = G.get_edge_data(students_left[x], students_left[y])['stress']

            if sij == 0:
                return [students_left[x], students_left[y]]

            if (hij / sij) > max_ratio and sij <= stress_limit:
                max_ratio = hij / sij
                max_pair = [students_left[x], students_left[y]]
            # print(hij, sij, hij / sij)

    return max_pair 


# G: the graph
# students_left: the students that have not been picked for a group yet
# stress_limit: the current stress limit
# group: the list containing the current members in our breakout group
#
# Returns the student i that has the highest ratio of happiness / stress once added to group such that
# total stress < stress_limit
# 
# If there exists no student that can be added to the group w/o breaking stress limit, return -1
#
# DOESNT CHANGE group OR students_left
def find_best_addition(G, students_left, stress_limit, group):
    max_ratio = 0
    max_addition = -1
    for x in range(len(students_left)):
        group.append(students_left[x])
        happiness = calculate_happiness_for_room(group, G)
        stress = calculate_stress_for_room(group, G)

        if stress == 0:
            return students_left[x]

        if (stress < stress_limit and (happiness / stress) > max_ratio):
            max_addition = students_left[x]
            max_ratio = happiness/stress
            # print(max_addition)
            # print(max_ratio)
        group.remove(students_left[x])

    return max_addition


# while the group has stress > stress_limit, remove the group member such that we retain the highest
# ratio of happiness / stress
#
# DOES CHANGE group and students_left
def trim_group(G, students_left, stress_limit, group):
    curr_stress = calculate_stress_for_room(group, G)
    while (curr_stress > stress_limit):
        best_removal = 0
        removed = group[0]
        for x in range(len(group)):
            student = group[x]
            group.remove(student)
            happiness = calculate_happiness_for_room(group, G)
            stress = calculate_stress_for_room(group, G)

            if stress == 0:
                removed = student 
                group.append(student)
                break

            if ((happiness / stress) > best_removal):
                best_removal = happiness / stress 
                removed = student
                # print("best_removal: " + str(best_removal))
                # print("removed:      "  + str(removed))
            group.append(student)

        group.remove(removed)
        students_left.append(removed)
        curr_stress = calculate_stress_for_room(group, G)
    

# Here's an example of how to run your solver.

# Usage: python3 solver.py test.in

# if __name__ == '__main__':
#     assert len(sys.argv) == 2
#     path = sys.argv[1]
#     G, s = read_input_file(path)
#     D, k = solve(G, s)
#     assert is_valid_solution(D, G, s, k)
#     print("Total Happiness: {}".format(calculate_happiness(D, G)))
#     write_output_file(D, 'outputs/small-1.out')


# For testing a folder of inputs to create a folder of outputs, you can use glob (need to import it)
if __name__ == '__main__':
    inputs = glob.glob('inputs/*')
    for input_path in inputs:
        print(input_path)
        output_path = 'outputs/' + basename(normpath(input_path))[:-3] + '.out'
        G, s = read_input_file(input_path)
        D, k, room_to_student = solve(G, s)
        
        print()
        print(room_to_student)
        print("# of rooms: " + str(k))
        print("stress limit: " + str(s / k))
        for i in range(k):
            print(str(i) + ": " + str(calculate_stress_for_room(room_to_student[i], G)))
        print()

        assert is_valid_solution(D, G, s, k)
        happiness = calculate_happiness(D, G)
        write_output_file(D, output_path)
