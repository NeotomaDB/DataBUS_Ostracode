import os
import re
from collections import Counter

def extract_unique_invalid_blocks(directory, output_file):
    error_counter = Counter()
    total_error_count = 0
    valid_block = False
    
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    # Read line by line for more precise control over block boundaries
                    for line in f:
                        line = line.strip()
                        # Start of a new validation block
                        if line.startswith("Valid: FALSE") or line.startswith("Valid: None") or line.startswith("There are multiple values"):
                            valid_block = True
                        # End of the current block
                        elif line.startswith("Valid:"):
                            valid_block = False
                        # Only capture errors within a valid block
                        if valid_block and line.startswith("✗"):
                            error_counter[line] += 1
                            total_error_count += 1
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
    
    # Print a summary of the error counts
    print(f"Total unique error blocks found: {error_counter}")
    print(f"Total error blocks found: {total_error_count}")
    print(f"Total files processed: {len(os.listdir(directory))}")
    
    # Return the unique error blocks as a list
    return list(error_counter.items()), total_error_count

def main():
    output_file='data/not_validated_blocks.txt'
    directory = 'data/NODE/validation_logs/not_validated/'
    errors, total_error_count = extract_unique_invalid_blocks(directory, output_file)
    # Save the unique blocks with counts to the output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for error, count in sorted(errors):
                f.write(f"{error} (Found {count} times)\n")
            f.write(f"\nTotal error blocks found: {total_error_count}\n")
        print(f"Output saved to {output_file}")
    except Exception as e:
        print(f"Error writing to output file {output_file}: {e}")

if __name__ == "__main__":
    main()