import csv
from typing import List, Optional
from graphviz import Digraph

class TreeNode:
    def __init__(self, question: Optional[str] = None, left=None, right=None, answers: Optional[List[str]] = None):
        # binary classification, Optional since we could be at a leaf that only has the answer/s
        self.question = question  
        self.left = left          # We go to the left if the answer to the question is no
        self.right = right        # We go to the right is the answer is yes
        # This will be filled out if we're at a leaf. We have an Optional list in case there's more than 1
        # answer at this leaf
        self.answers = answers if answers else []  

    #If the answers list is empty, we're at a leaf node so True is returned
    def is_leaf(self):
        return bool(self.answers)  

def read_csv(filename: str):
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)  # Create a CSV reader object to iterate over rows
        rows = list(reader)  # Read all rows from the CSV file into a list of lists

        header = rows[0]  # The first row is assumed to be the header containing column names
        features = header[1:]  # Extract feature names by slicing the header from the second element onwards
        label_col_index = 0  # Assume the label column is the first column (index 0)
        label_col = header[label_col_index]  # Get the name of the label column from the header

        data_rows = rows[1:]  # Extract the data rows by slicing the list of rows, excluding the header

        rows_as_dicts = []  # Initialize an empty list to store rows as dictionaries
        for row in data_rows:
            # Create a dictionary for each data row, mapping header names to row values
            row_dict = {header[i]: row[i] for i in range(len(header))}
            rows_as_dicts.append(row_dict)  # Add the created dictionary to the list

        return rows_as_dicts, features, label_col  # Return the processed data.

def all_same_values(rows: List[dict], col_names: List[str]):
    """Check if all rows have the same values for the given columns."""
    if not rows:  # Check if there are no rows
        return True  
    first_row_values = [rows[0][col] for col in col_names]  # Get the values of the specified columns from the first row
    return all(
        [all(row[col] == first_row_values[i] for i, col in enumerate(col_names)) for row in rows[1:]]
        # Iterate through the remaining rows (starting from the second row)
        # For each row, check if the values in the specified columns are the same
        # as the corresponding values in the first row
        # The outer 'all()' function returns True only if the inner 'all()' is True for all remaining rows
    )

def best_split(rows: List[dict], classifications: List[str]):
    """Find the feature that creates the most balanced split."""

    best_classification = None  # Initialize the best classification feature found so far
    best_balance = float('inf')  # Initialize the best balance found so far to infinity

    for classification in classifications:  # Iterate through each classification feature
        # Count the number of rows where the value of the current classification feature is '0' (after stripping whitespace)
        count_0 = sum(1 for row in rows if row[classification].strip() == '0')
        # Count the number of rows where the value of the current classification feature is '1' (after stripping whitespace)
        count_1 = sum(1 for row in rows if row[classification].strip() == '1')
        # Calculate the balance of the split as the absolute difference between the counts
        balance = abs(count_0 - count_1)

        # Check if the current split is valid (both groups are non-empty and smaller than the total number of rows)
        # and if the current balance is better (smaller) than the best balance found so far
        if 0 < count_0 < len(rows) and 0 < count_1 < len(rows) and balance < best_balance:
            best_classification = classification  # Update the best classification 
            best_balance = balance  # Update the best balance

    return best_classification  # Return the feature that resulted in the most balanced split

def build_tree(rows: List[dict], classifications: List[str], label_col: str) -> TreeNode:
    if not rows:  # If there are no rows, return a leaf node with no answers
        return TreeNode(answers=[])  # Indicates an empty branch or no data to classify

    # If all rows have the same value for the label column and all classifications,
    # or if there are no classifications left to split on in the subsequent check,
    # we have reached a leaf node
    if all_same_values(rows, [label_col] + classifications):
        # Create a leaf node with all the labels from the current rows
        # This handles cases where multiple identical data points with the same label exist
        return TreeNode(answers=[row[label_col] for row in rows])

    # Find the best classification to split the current set of rows
    best_classification = best_split(rows, classifications)

    # If there are no classifications left to split on, or if best_split
    # returns None (meaning no good split could be found), create a leaf node
    # with the labels from the current rows
    if not classifications or not best_classification:
        return TreeNode(answers=[row[label_col] for row in rows])

    # Create subsets of the rows based on the best classification's values ('0' and '1').
    left_split = [row for row in rows if row[best_classification].strip() == '0']
    right_split = [row for row in rows if row[best_classification].strip() == '1']

    # Create a new list of classifications for the child nodes, excluding the classification we just split on
    remaining_classifications = [c for c in classifications if c != best_classification]

    # Recursively build the left subtree using the left split and the remaining classifications.
    left_child = build_tree(left_split, remaining_classifications, label_col)
    # Recursively build the right subtree using the right split and the remaining classifications.
    right_child = build_tree(right_split, remaining_classifications, label_col)

    # Create the current internal node with the best classification as the question
    # and the recursively built left and right children.
    return TreeNode(question=best_classification, left=left_child, right=right_child)

#Method to print the tree in a nice way
def print_tree(node: TreeNode, prefix: str = '', is_left: bool = True):
    if node is None:
        return

    branch = '├── ' if is_left else '└── '
    connector = prefix + branch

    if node.is_leaf():
        print(connector + f"[Guess(es)] {', '.join(node.answers)}") # Print multiple answers
    else:
        print(connector + f"Q: {node.question}?")
        extension = '│   ' if is_left else '    '
        print_tree(node.left, prefix + extension, True)
        print_tree(node.right, prefix + extension, False)

def ask_yes_no(prompt: str) -> bool:
    while True:
        response = input(prompt + ' (yes/no): ').strip().lower() #ask a question
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please answer 'yes' or 'no'.") #catch unexpected input

def play_game(tree: TreeNode):
    print("\nThink of an element from the dataset. I will try to guess which one it is!\n")
    node = tree #to start traversing the tree
    guesses = 0 #keep track of how many guesses the program has made
    guessed_elements = [] # Keep track of guesses in case of multiple answers

    #keep asking questions about the classifications as long as we're not at a leaf
    while not node.is_leaf():
        answer = ask_yes_no(f"{node.question}")
        node = node.right if answer else node.left #go to the right if the answer is yes, go left otherwise
        guesses += 1 #increment # of guesses

    # We reach this point once we're at a leaf, guessed_elements is set to be the list of answers that we have 
    #at this leaf
    guessed_elements = node.answers 

    #If there's only 1 possible answer, only ask about this
    if len(guessed_elements) == 1:
        correct = ask_yes_no(f"Is your guess {guessed_elements[0].strip()}?")
        guesses += 1
        if correct:
            print(f"Yay! I guessed it in {guesses} questions!")
        else: #if our one answer wasn't what the user had in mind
            print(f"Well played! I couldn't guess your element. I used {guesses} questions.")
    #In the case we have more than 1 in our answers
    elif len(guessed_elements) > 1:
        correct = False
        # Traverse the elements in our answers list and ask about each one
        for element in guessed_elements:
            answer = ask_yes_no(f"Is your guess {element.strip()}?")
            guesses += 1
            if answer:
                correct = True
                print(f"Yay! I guessed it in {guesses} questions!")
                break
        if not correct:
            print(f"Well played! I couldn't guess your element. I used {guesses} questions.")
    else:
        print("I couldn't make a guess.") # Handle empty list

#method to create a nice graph of the tree
def export_tree_to_png(root: TreeNode, filename: str = "tree_visual.png"):
    dot = Digraph()
    node_id = 0  # Unique node IDs to avoid conflicts

    def add_nodes_edges(node: TreeNode, parent_id: Optional[str] = None, edge_label: Optional[str] = ""):
        nonlocal node_id
        current_id = str(node_id)
        node_id += 1

        if node.is_leaf():
            label = "Guess(es): " + ", ".join(node.answers)
            dot.node(current_id, label, shape='box', style='filled', color='lightgrey')
        else:
            label = f"Q: {node.question}?"
            dot.node(current_id, label, shape='ellipse')

        if parent_id is not None:
            dot.edge(parent_id, current_id, label=edge_label)

        if not node.is_leaf():
            add_nodes_edges(node.left, current_id, "no")
            add_nodes_edges(node.right, current_id, "yes")

    add_nodes_edges(root)
    dot.render(filename, format="png", cleanup=True)
    print(f"Tree image saved as {filename}")

def main():
    #reading the file
    filename = 'painters.csv'
    rows, features, label_col = read_csv(filename)
    tree = build_tree(rows, features, label_col)
    export_tree_to_png(tree)

    #print the tree for better visualization/debugging
    #print("Visual Tree Structure:\n")
    #print_tree(tree)

    #ask if the user wants to keep playig or not after each game
    while True:
        play_game(tree)
        if not ask_yes_no("Would you like to play again?"):
            print("Goodbye!")
            break

if __name__ == '__main__':
    main()
