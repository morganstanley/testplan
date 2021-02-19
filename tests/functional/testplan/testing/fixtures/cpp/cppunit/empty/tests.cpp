#ifndef __cppunit_example__
#define __cppunit_example__

#include <unistd.h>

#include <iostream>
#include <string>

#include <cppunit/TestCase.h>
#include <cppunit/TestFixture.h>
#include <cppunit/TestResult.h>
#include <cppunit/TestResultCollector.h>
#include <cppunit/TestRunner.h>
#include <cppunit/extensions/TestFactoryRegistry.h>
#include <cppunit/extensions/HelperMacros.h>
#include <cppunit/XmlOutputter.h>

using namespace CPPUNIT_NS;

using std::cerr;
using std::cout;
using std::endl;
using std::string;
using std::ofstream;

static const int RET_OK = 0;
static const int RET_USAGE = -1;
static const int RET_BAD_TEST = -2;


void usage(const char *path)
{
  string image(path);
  image = image.substr(image.find_last_of("/\\") + 1);

  cout << endl;
  cout << "Usage: " << image << " [ -l | -h | -t test]" << endl << endl;

  cout << "A test example built against cppunit version: ";
  cout << CPPUNIT_VERSION << endl << endl;

  cout << "Options:" << endl;
  cout << "    -t  Runs the given test only. Default: All Tests" << endl;
  cout << "    -l  List all available tests." << endl;
  cout << "    -h  Print this usage message." << endl << endl;

  cout << "Returns:" << endl;
  cout << "    0 on success" << endl;
  cout << "    positive for number of errors and failures" << endl;
  cout << "    otherwise no test ever runs" << endl << endl;
}

// Recursive dumps the given Test heirarchy to cout
void dump(Test *test, int depth)
{
  if (test == 0) {
    return;
  }

  if (test->getName() == "All Tests") {
    for (int i = 0; i < test->getChildTestCount(); i++) {
      dump(test->getChildTestAt(i), 0);
    }
  }
  else {
    for (int i = 0; i < depth; ++i)
      cout << "  ";

    if (depth == 0) {
      cout << test->getName() << "." << endl;
    }
    else {
      string testName = test->getName();
      cout << testName.substr(testName.find_last_of(":") + 1) << endl;
    }

    for (int i = 0; i < test->getChildTestCount(); i++) {
      dump(test->getChildTestAt(i), depth + 1);
    }
  }
}

// Recursively seeks test matching the given filter, otherwise returns 0.
Test *find(Test *test, const string &name)
{
  if (test == 0) {
    return 0;
  }

  string testName = test->getName();
  if (testName == name
      || testName.substr(testName.find_last_of(":") + 1) == name) {
    return test;
  }

  for (int i = 0; i < test->getChildTestCount(); i++) {
    Test *found = find(test->getChildTestAt(i), name);
    if (found) {
      return found;
    }
  }

  return 0;
}


int main(int argc, char **argv)
{
  TestResult result;
  // register listener for collecting the test-results
  TestResultCollector collector;
  result.addListener(&collector);

  Test *test = 0;
  char flag = 0;
  string filter = "";
  string fileOut = "";

  while ((flag = getopt(argc, argv, "t:y:lh")) != -1) {

    switch(flag) {

    case 'l':
      {
        dump(TestFactoryRegistry::getRegistry().makeTest(), 0);
        return RET_OK;
      }

    case 't':
      {
        filter = optarg;
      }
      break;

    case 'y':
      {
        fileOut = optarg;
      }
      break;

    case 'h':
    default:
      usage(argv[0]);
      return RET_USAGE;
    }
  }

  if (filter.length())
    test = find(TestFactoryRegistry::getRegistry().makeTest(), filter);
  else
    test = TestFactoryRegistry::getRegistry().makeTest();

  if (test == 0) {
    cerr << "No test case found" << endl;
    return RET_BAD_TEST;
  }

  TestRunner runner;
  runner.addTest(test);
  runner.run(result);

  if (fileOut.length()) {
    ofstream xmlFileOut(fileOut);
    Outputter *outputter = new XmlOutputter(&collector, xmlFileOut);
    outputter->write();
  }
  else {
    Outputter *outputter = new XmlOutputter(&collector, cout);
    outputter->write();
  }

  return collector.testErrors() + collector.testFailures();

}

#endif // __cppunit_example__

