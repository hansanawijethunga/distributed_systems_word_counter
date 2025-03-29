import PyPDF2
import pandas as pd
import string


# Function to extract text from the PDF
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text


# Function to count words starting with each letter
def count_starting_letters(pdf_path):
    text = extract_text_from_pdf(pdf_path).lower()  # Convert text to lowercase
    letter_count = {letter: 0 for letter in string.ascii_lowercase}  # Initialize count for each letter
    line_count_details = []  # To store line-by-line details
    cumulative_count = {letter: 0 for letter in string.ascii_lowercase}  # Initialize cumulative count

    lines = text.split('\n')  # Split text into lines

    for line_number, line in enumerate(lines, 1):
        line_words = line.split()  # Split the line into words
        line_letter_count = {letter: 0 for letter in
                             string.ascii_lowercase}  # Initialize count for each letter in the line

        # Count words starting with each letter in the line
        for word in line_words:
            first_letter = word[0]
            if first_letter in line_letter_count:
                line_letter_count[first_letter] += 1

        # Update the global letter count and cumulative count
        for letter, count in line_letter_count.items():
            letter_count[letter] += count
            cumulative_count[letter] += count

        line_count_details.append((line_number, line, line_letter_count, len(line_words),
                                   cumulative_count.copy()))  # Store the line, counts, and cumulative counts

    return letter_count, line_count_details


# Function to display the results in a table and save as CSV
def display_and_save_results(letter_count, line_count_details, csv_prefix="output"):
    # Convert the result into a pandas DataFrame for better visualization
    data = {'Letter': [], 'Count': []}

    for letter, count in letter_count.items():
        data['Letter'].append(letter.upper())  # Capitalize the letter
        data['Count'].append(count)

    # Create a DataFrame for the letter counts and save as CSV
    df = pd.DataFrame(data)
    df.to_csv(f"{csv_prefix}_letter_count.csv", index=False)

    # Line by line details with cumulative count
    cumulative_data = {'Line Number': [], 'Letter': [], 'Cumulative Count': []}
    for line_number, line, line_letter_count, word_count, cumulative in line_count_details:
        print(f"Line {line_number}: {line}")
        print(f"Word Count: {word_count}")
        print(f"Letter Count: {line_letter_count}")
        print(f"Cumulative Count: {cumulative}")
        print("-" * 50)

        # Prepare data for cumulative count table
        for letter, count in cumulative.items():
            cumulative_data['Line Number'].append(line_number)
            cumulative_data['Letter'].append(letter.upper())
            cumulative_data['Cumulative Count'].append(count)

    # Create a DataFrame for the cumulative counts and save as CSV
    cumulative_df = pd.DataFrame(cumulative_data)
    cumulative_df.to_csv(f"{csv_prefix}_cumulative_count.csv", index=False)

    # Total word count
    total_word_count = sum(word_count for _, _, _, word_count, _ in line_count_details)
    print(f"\nTotal Word Count: {total_word_count}")

    # Save total word count to a CSV file
    total_word_count_df = pd.DataFrame({'Total Word Count': [total_word_count]})
    total_word_count_df.to_csv(f"{csv_prefix}_total_word_count.csv", index=False)


# Path to your PDF file
pdf_path = "Material/Document.pdf"

# Get the starting letter count and line-by-line details
letter_count, line_count_details = count_starting_letters(pdf_path)

# Display the result in a table and save the results as CSV files
display_and_save_results(letter_count, line_count_details, csv_prefix="Material/Document")
