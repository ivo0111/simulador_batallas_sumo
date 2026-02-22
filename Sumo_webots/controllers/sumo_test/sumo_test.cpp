#include <webots/Robot.hpp>
#include <webots/Motor.hpp>
#include <webots/DistanceSensor.hpp>
#include <iostream>

using namespace webots;

#define TIME_STEP 32

int main()
{
    std::cout << "iniciando robot" << std::endl;
    Robot robot;

    Motor *left = robot.getMotor("left_motor");
    Motor *right = robot.getMotor("right_motor");

    left->setPosition(INFINITY);
    right->setPosition(INFINITY);

    left->setVelocity(0);
    right->setVelocity(0);

    DistanceSensor *lineL = robot.getDistanceSensor("line_left");
    DistanceSensor *lineR = robot.getDistanceSensor("line_right");
    DistanceSensor *ir = robot.getDistanceSensor("front_ir");

    
    lineL->enable(TIME_STEP);
    lineR->enable(TIME_STEP);
    ir->enable(TIME_STEP);
    
    while (robot.step(TIME_STEP) != -1)
    {
        
        double l = lineL->getValue();
        double r = lineR->getValue();
        double irv = ir->getValue();
        
        bool edge = (l < 200 || r < 200);
        bool enemy = (irv > 500);

        if (edge)
        {
            left->setVelocity(-10);
            right->setVelocity(-10);
        }
        else if (enemy)
        {
            left->setVelocity(15);
            right->setVelocity(15);
        }
        else
        {
            left->setVelocity(4);
            right->setVelocity(-4);
        }
    }
}
