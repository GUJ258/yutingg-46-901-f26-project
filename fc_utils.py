import copy
import heapq

class PQ:
    counter = 0

    def __init__(self, key):
        self.L = []
        self.key = key

    def __repr__(self):
        # TODO: Print this out as a tree
        return str([elem[2] for elem in self.L])

    def isEmpty(self):
        return self.L == []

    def size(self):
        return len(self.L)

    def peek(self):
        key, _, v = self.L[0]
        return v

    def pop(self):
        key, _, v = heapq.heappop(self.L)
        return v

    def push(self, v):
        heapVal = (self.key(v), PQ.counter, v)
        heapq.heappush(self.L, heapVal)
        PQ.counter += 1


class Tree:
    def __init__(self, value, *children):
        self.value = value
        self.children = children

    def __str__(self):
        return self.toString()

    def __repr__(self):
        if self.isLeaf():
            return f'Tree({repr(self.value)})'
        else:
            childStrs = [repr(child) for child in self.children]
            children = ', '.join(childStrs)
            return f'Tree({repr(self.value)}, {children})'

    def __eq__(self, other):
        return (
            isinstance(other, Tree)
            and (self.value == other.value)
            and (len(self.children) == len(other.children))
            and (
                all(
                    [
                        myChild == otherChild
                        for myChild, otherChild in zip(self.children, other.children)
                    ]
                )
            )
        )

    def getValue(self):
        return self.value

    def getChildren(self):
        return self.children

    def isLeaf(self):
        return len(self.children) == 0

    def addChild(self, child):
        if not isinstance(child, Tree):
            raise Exception('The child is not a Tree object.')
        if self._containsTree(child):
            raise Exception('The child tree is already in this tree.')
        self.children += (child,)

    def removeChild(self, child):
        if child not in self.children:
            raise Exception('The tree is not a child of this tree.')
        i = self.children.index(child)
        self.children = self.children[:i] + self.children[i + 1 :]

    def _containsTree(self, Tree):
        if self is Tree:
            return True
        for child in self.children:
            if child._containsTree(Tree):
                return True
        return False

    def toString(self, compact=False, symmetric=False):
        if compact:
            return self.vshow()
        else:
            return self.hshow(symmetric)

    def vshow(self):
        def walk(tree, prefix1, prefix2):
            lines = [prefix1 + str(tree.value)]
            for i in range(len(tree.children)):
                lastChild = i == len(tree.children) - 1
                c1, c2 = ('└', ' ') if lastChild else ('├', '│')
                lines.append(
                    walk(tree.children[i], prefix2 + c1 + '── ', prefix2 + c2 + '   ')
                )
            return '\n'.join(lines)

        return walk(self, '', '')

    def hshow(self, symmetric=False):
        padLengths = self._lengthsByLevel()
        paddedTree = self._padValues(padLengths)
        hshowList = paddedTree._hshowHelper(symmetric)
        # return hshowList
        return '\n'.join(''.join(row) for row in hshowList)

    # Assumes the tree is padded (by calling ._padValues), and all the values
    # are strings (which ._padValues) also does
    # Horizontal: chr(0x2500)
    # Vertical: chr(0x2502)
    # Top corner: chr(0x250c)
    # Bottom corner: chr(0x2514)
    def _hshowHelper(self, symmetric=False):
        if self.isLeaf():
            return [[chr(0x2500), chr(0x2500), chr(0x2500), str(self.value)]]
        else:
            childLists = []
            for child in self.children:
                childLists.append(child._hshowHelper(symmetric))
            # Pad each child tree to the larger of itself and its symmetric tree
            if symmetric:
                for i in range(len(childLists) // 2):
                    L1 = childLists[i]
                    L2 = childLists[-i - 1]
                    maxHeight = max(len(L1), len(L2))
                    Tree._padTreeToHeight(L1, maxHeight)
                    Tree._padTreeToHeight(L2, maxHeight)
            # Combine all the child lists vertically, leaving space in the front
            # for the current element, and 1 row of space between each child
            valueLen = len(self.value)
            frontPadding = 7 + valueLen
            for childList in childLists:
                for row in childList:
                    for _ in range(frontPadding):
                        row.insert(0, ' ')
            result = []
            for i in range(len(childLists)):
                result.extend(copy.deepcopy(childLists[i]))
                result.append([' '] * frontPadding)
            result.pop()  # remove the extra empty list added at the end
            # Insert the element and horizontal lines on either side of it
            midRow = len(result) // 2
            result[midRow][0] = chr(0x2500)
            result[midRow][1] = chr(0x2500)
            result[midRow][2] = chr(0x2500)
            for i in range(valueLen):
                result[midRow][3 + i] = self.value[i]
            result[midRow][3 + valueLen] = chr(0x2500)
            result[midRow][4 + valueLen] = chr(0x2500)
            result[midRow][5 + valueLen] = chr(0x2500)
            # Add the vertical lines connecting all the children
            startRow = len(childLists[0]) // 2
            endRow = len(result) - len(childLists[-1]) // 2
            if startRow == endRow - 1:  # if there's only 1 child just make -
                result[startRow][6 + valueLen] = chr(0x2500)
            else:  # If more than 1 child, make top and bottom corners
                result[startRow][6 + valueLen] = chr(0x250C)
                result[endRow - 1][6 + valueLen] = chr(0x2514)
            for row in range(startRow + 1, endRow - 1):
                left = result[row][5 + valueLen]
                right = (
                    result[row][7 + valueLen]
                    if (7 + valueLen < len(result[row]))
                    else ' '
                )
                if left != ' ' and right != ' ':  # character is +
                    c = chr(0x253C)
                elif left != ' ':  # character is -|
                    c = chr(0x2524)
                elif right != ' ':  # character is |-
                    c = chr(0x251C)
                else:  # character is |
                    c = chr(0x2502)
                result[row][6 + valueLen] = c
            return result

    # Returns a dictionary mapping each level to the max length of a value at
    # that level
    def _lengthsByLevel(self, level=0):
        res = {level: len(str(self.value))}
        for child in self.children:
            childLengths = child._lengthsByLevel(level + 1)
            for lvl, length in childLengths.items():
                if lvl in res:
                    res[lvl] = max(res[lvl], length)
                else:
                    res[lvl] = length
        return res

    # Creates a new tree with all values converted to a string
    # Values at the leaves do not change
    # Other values are padded with '-' on either side to the length of the
    # max length value in that level of the tree
    def _padValues(self, padLengths, level=0):
        if self.isLeaf():
            return Tree(str(f' {self.value} '))
        else:
            length = padLengths[level]
            paddedVal = Tree._padValue(self.value, length)
            paddedChildren = [
                child._padValues(padLengths, level + 1) for child in self.children
            ]
            return Tree(paddedVal, *paddedChildren)

    @staticmethod
    def _padValue(val, length):
        valStr = str(val)
        lengthDiff = length - len(valStr)
        leftPad = lengthDiff // 2
        rightPad = lengthDiff - leftPad
        return (chr(0x2500) * leftPad) + f' {val} ' + (chr(0x2500) * rightPad)

    @staticmethod
    def _padTreeToHeight(L, height):
        heightDiff = height - len(L)
        padding = heightDiff // 2
        for _ in range(padding):
            L.insert(0, [])
            L.append([])

    @staticmethod
    def fromVshowString(vshowString, valueType=str):
        lines = vshowString.splitlines()
        root = Tree(valueType(lines[0]))
        openTrees = [root]
        for line in lines[1:]:
            i = line.rfind('── ') + 3
            depth = i // 4
            openTrees = openTrees[:depth]
            child = Tree(valueType(line[i:]))
            openTrees[-1].addChild(child)
            openTrees.append(child)
        return root


class BinaryTree:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self._left = left
        self._right = right

    def _convertToTree(self):
        if self.isLeaf():
            return Tree(self.getValue())
        else:
            leftTree = self.getLeft()
            rightTree = self.getRight()
            children = []
            if leftTree is not None:
                children.append(leftTree._convertToTree())
            if rightTree is not None:
                children.append(rightTree._convertToTree())
            return Tree(self.getValue(), *children)

    def __str__(self):
        return str(self._convertToTree())

    def __repr__(self):
        if self.isLeaf():
            return f'Tree({self.value}, {self._left}, {self._right})'
        else:
            leftRepr = repr(self._left)
            rightRepr = repr(self._right)
            return f'Tree({self.value}, {leftRepr}, {rightRepr})'

    def __eq__(self, other):
        if not isinstance(other, BinaryTree):
            return False
        return (
            (self.getValue() == other.getValue())
            and (self._left == other._left)
            and (self._right == other._right)
        )

    def isLeaf(self):
        return self._left is None and self._right is None

    def getValue(self):
        return self.value

    def getLeft(self):
        return self._left

    def getRight(self):
        return self._right

    def getChildren(self):
        return (self._left, self._right)

    def getSize(self):
        if self.isLeaf():
            return 1
        else:
            leftSize = 0 if self.getLeft() is None else self.getLeft().getSize()
            rightSize = 0 if self.getRight() is None else self.getRight().getSize()
            return leftSize + rightSize + 1


class BST(BinaryTree):
    def __init__(self, value=None):
        if value is None:
            self.hasNode = False
            super().__init__(None)
            self.size = 0
        else:
            self._initFirstNode(value)

    def _initFirstNode(self, value):
        self.hasNode = True
        super().__init__(value)
        self.size = 1

    def getSize(self):
        return self.size

    def insert(self, value):
        # TODO: Perform rotations to maintain balance
        if not self.hasNode:
            self._initFirstNode(value)
            return

        self.size += 1
        if value > self.getValue():
            rightTree = self.getRight()
            if rightTree is None:
                self._right = BST(value)
            else:
                rightTree.insert(value)
        else:
            leftTree = self.getLeft()
            if leftTree is None:
                self._left = BST(value)
            else:
                leftTree.insert(value)

    @staticmethod
    def fromList(L):
        t = BST()
        for v in L:
            t.insert(v)
        return t


__all__ = ['PQ', 'Tree', 'BinaryTree', 'BST']
