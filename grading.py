
import unittest
import os
import Query
import FlightService
import concurrent.futures
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
import time
from multiprocessing import Process
import apsw
class User:
    def __init__(self, cmds, results):
        self.cmds = cmds
        self.results = results

    def call(self):
        self.q = Query.Query()
        outputBuffer = ""
        for cmd in self.cmds:
            outputBuffer += FlightService.execute(self.q, cmd)      
        return outputBuffer
    
    def toString(self):
        print("cmds:", self.cmds)
        print("results:", self.results)


COMMENTS = "#"
DELIMITER = "*"
SEPERATOR = "|"

RESET_DB_NAME = "reset.db"

def resetDb():
    # Remove old DB file
    os.remove(Query.DB_NAME)

    # Check if the reset DB file exists
    if os.path.isfile(RESET_DB_NAME):
        # File exists, just copy it over
        os.system("cp {} {}".format(RESET_DB_NAME, Query.DB_NAME))
    else:
        # File does not exist, remake the file
        q = Query.Query()
        q.clearTables()

        # Create the reset file based on current file
        os.system("cp {} {}".format(Query.DB_NAME, RESET_DB_NAME))
        os.system("chmod 777 {}".format(RESET_DB_NAME))

    os.system("chmod 777 {}".format(Query.DB_NAME))

def parse_testcase(testcase_filename):
    users = []
    cmds = []
    results = []
    output_buffer = ""
    with open(testcase_filename, 'r') as f:
        lines = f.readlines()
        isCMD = True
        for line in lines:
            if(line[0] == COMMENTS):#comments that should be ignored
                continue
            elif(line[0] == DELIMITER):
                if(isCMD == True):
                    isCMD = False
                else:#end of current user's possible results
                    results.append(output_buffer)
                    users.append(User(cmds, results))
                    #print(User(cmds, results).toString())
                    cmds = []
                    results = []
                    output_buffer = ""
                    isCMD = True
            elif(line[0] == SEPERATOR):
                if(isCMD == True):
                    raise Exception("wrong testcase format!")
                else:
                    results.append(output_buffer)
                    output_buffer = ""
            else:
                line_without_comments = line.split("#", 2)[0]
                if(isCMD):
                    cmds.append(line_without_comments)
                else:
                    output_buffer += line_without_comments
    # for user in users:
    #     print(user.toString())
    return users
            
class TestFlightService(unittest.TestCase):

    def test_non_concurrency(self):
        exitCode = 0

        non_concurrent_testcases = os.listdir("testcases/non_concurrent/")
        counter = 0
        score = 0
        for testcase in non_concurrent_testcases:
            resetDb()
            users = parse_testcase(os.path.join("testcases/non_concurrent/", testcase))
            counter +=1
            passed = True
            for user in users:
                output = user.call()
                if(output != user.results[0]):
                    passed = False
                    print("testcase {} fails, score for non_concurrent test {}/{}".format(testcase, score,counter))
                    print("your output for testcase {} is:\n {}".format(testcase, output))
                    exitCode = 1
            if(passed):
                score +=1
                print("testcase {} passes, score for non_concurrent test {}/{}".format(testcase, score,counter))

        assert exitCode == 0

    def test_concurrency(self):
        exitCode = 0

        concurrent_testcases = os.listdir("testcases/concurrent/")
        counter = 0
        score = 0
        for testcase in concurrent_testcases:
            users = parse_testcase(os.path.join("testcases/concurrent/", testcase))
            with ProcessPoolExecutor(max_workers=3) as executor:
                #multiple test for each concurrent testcase
                for i in range(5):
                    time.sleep(1)
                    counter += 1
                    resetDb()
                    futures = []
                    for user in users:
                        futures.append(executor.submit(user.call))
                    passed = False
                    for k in range(len(users[0].results)):
                        #you only need pass one of the possible outputs. concurrent execution is non-deterministic
                        if(futures[0].result().strip() == users[0].results[k].strip() and futures[1].result().strip() == users[1].results[k].strip()):
                            passed = True
                    if(passed == True):
                        score +=1
                        print("testcase {} passes, score for concurrent tests so far: {}/{}".format(testcase, score, counter))
                    else:
                        print("testcase {} fails, score for concurrent tests so far: {}/{}".format(testcase, score, counter))
                        print("your output for testcase {}\n\n user1 :\n {}\n\n user2 :\n {}\n\n".format(testcase, futures[0].result().strip(), futures[1].result().strip()))
                        exitCode = 1
        
        assert exitCode == 0

if __name__ == '__main__':
    if os.path.isfile(RESET_DB_NAME):
        os.remove(RESET_DB_NAME)

    unittest.main()
