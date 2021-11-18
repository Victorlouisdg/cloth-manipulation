import bpy
import sys
import argparse


def test_print():
    print("test worked!")
    print(bpy.context.scene)


if __name__ == "__main__":
    test_print()