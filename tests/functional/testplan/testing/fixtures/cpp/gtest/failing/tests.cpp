#include "app.cpp"
#include <gtest/gtest.h>

TEST(SquareRootTest, PositiveNos) {
  ASSERT_EQ(6, squareRoot(36.0));
  ASSERT_EQ(4, squareRoot(36.0));
  ASSERT_EQ(2, squareRoot(10.0));
  ASSERT_EQ(18.0, squareRoot(324.0));
  ASSERT_EQ(25.4, squareRoot(645.16));
  ASSERT_EQ(0, squareRoot(0.0));
}


TEST(SquareRootTest, NegativeNos) {
  ASSERT_EQ(-1.0, squareRoot(-15.0));
  ASSERT_EQ(-1.0, squareRoot(-0.2));
}

TEST(SquareRootTestNonFatal, PositiveNos) {
  EXPECT_EQ(6, squareRoot(36.0));
  EXPECT_EQ(4, squareRoot(36.0));
  EXPECT_EQ(2, squareRoot(10.0));
  EXPECT_EQ(18.0, squareRoot(324.0));
  EXPECT_EQ(25.4, squareRoot(645.16));
  EXPECT_EQ(0, squareRoot(0.0));
}

TEST(SquareRootTestNonFatal, NegativeNos) {
  EXPECT_EQ(-1.0, squareRoot(-15.0));
  EXPECT_EQ(-1.0, squareRoot(-0.2));
}


int main(int argc, char **argv) {
  testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
