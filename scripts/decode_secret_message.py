import requests
import re
from bs4 import BeautifulSoup

def decode_secret_message(url: str):
    """
    Decode the secret message from the given URL
    :param url:
    :return:
    """
    if not url:
        print("URL is required")
        return
    if not url.startswith("http"):
        print("Invalid URL")
        return
    response = requests.get(url)
    if response.status_code != 200:
        print(response.text)
        print("Getting the document failed.")
        return
    data = response.text
    soup = BeautifulSoup(data, "html.parser")
    xy_character_table = soup.find("table")
    if not xy_character_table:
        print("No table found in the document.")
        return

    # Extract the characters from the table
    # Data example: ["0█0", "0█1", "0█2", "1▀1", "1▀2", "2▀1", "2▀2", "3▀2"]
    # value format: "{x}{character}{y}"
    xy_character_rows = [content.get_text() for content in xy_character_table.contents[1::]]

    # List to hold tuples of (x, y, character)
    positions = []

    # Process each row in the table
    for row in xy_character_rows:
        # Extract x, y, and character from the row
        x, character, y = re.match(r"(\d+)(.)(\d+)", row).groups()

        # Convert x and y to integers
        x, y = int(x), int(y)

        # Append the position and character to the list
        positions.append((x, y, character))

    # Check that we found some valid positions
    if not positions:
        print("No valid data found in the document.")
        return

    # Determine grid boundaries
    x_size = [x for x, _, _ in positions]
    y_size = [y for _, y, _ in positions]
    min_x, max_x = min(x_size), max(x_size)
    min_y, max_y = min(y_size), max(y_size)
    width = max_x - min_x + 1
    height = max_y - min_y + 1

    # Create a grid filled with space characters
    grid = [[" " for _ in range(width)] for _ in range(height)]

    # Place each character at its corresponding coordinate.
    # Here, (min_x, max_y) is assumed to be the top-left corner of the grid
    for x, y, ch in positions:
        grid[max_y - y][x - min_x] = ch

    # Print the grid
    for row in grid:
        print("".join(row))


if __name__ == '__main__':
    # doc_url = "https://docs.google.com/document/d/e/2PACX-1vRMx5YQlZNa3ra8dYYxmv-QIQ3YJe8tbI3kqcuC7lQiZm-CSEznKfN_HYNSpoXcZIV3Y_O3YoUB1ecq/pub"
    doc_url = "https://docs.google.com/document/d/e/2PACX-1vQGUck9HIFCyezsrBSnmENk5ieJuYwpt7YHYEzeNJkIb9OSDdx-ov2nRNReKQyey-cwJOoEKUhLmN9z/pub"
    decode_secret_message(doc_url)
