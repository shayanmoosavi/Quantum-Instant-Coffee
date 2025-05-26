"""Module for fetching the atomic weights, names and labels of elements from IUPAC website.

This module performs the following tasks:
1. Fetches the atomic data table from the IUPAC website.
2. Processes the table to clean and structure the data.
3. Stores the processed data in a SQLite database.
"""

import sqlite3
import os
from io import StringIO
from typing import List

import requests
from bs4 import BeautifulSoup
import pandas as pd

from input.generators.sections import InputGenerationError


# Fetching the webpage
def fetch_elements_data(url: str = "https://iupac.qmul.ac.uk/AtWt/"):
    """
    Fetches the atomic weights, names, and labels of elements from the IUPAC website.

    Args:
        url (str): The URL of the IUPAC website containing the atomic data table.

    Returns:
        BeautifulSoup.Tag: The HTML table containing the atomic data.

    Raises:
        SystemExit: If the webpage cannot be retrieved or the table is not found.
    """
    print(f"Fetching data from {url}...")
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to retrieve the webpage (status code: {response.status_code})")
        exit(1)

    # Parse the HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # Locate the table with atomic data
    table_2_name = soup.find("a", {"name": "02"})
    table_2_html = table_2_name.find_next("table")

    if not table_2_html:
        print("Could not find the table")
        exit(1)
    return table_2_html


def process_elements_data(html_data) -> pd.DataFrame:
    """
    Processes the HTML table containing atomic data into a cleaned pandas DataFrame.

    Args:
        html_data (BeautifulSoup.Tag): The HTML table containing the atomic data.

    Returns:
        pandas.DataFrame: A cleaned DataFrame with atomic data.

    The DataFrame contains the following columns:
        - Atomic Number: The atomic number of the element.
        - Symbol: The chemical symbol of the element.
        - Element Name: The name of the element.
        - Atomic Weight: The atomic weight of the element (cleaned and converted to numeric).
    """
    # Extract the table data
    data = pd.read_html(StringIO(str(html_data)), header=0)[0]

    # Renaming the columns for better readability
    data.columns = ["Atomic Number", "Symbol", "Element Name", "Atomic Weight", "Notes"]

    # Dropping the "Notes" column as it is not needed
    data.drop("Notes", axis=1, inplace=True)

    # Setting the index column to "Atomic Number"
    data.set_index("Atomic Number", inplace=True)

    # Cleaning up the data
    # ------------------------------------------------------------------------------------------

    # Remove unstable element weights enclosed in brackets
    data["Atomic Weight"] = data["Atomic Weight"].str.replace(r"\[.*?]", "", regex=True)

    # Remove uncertainty in atomic weights
    data["Atomic Weight"] = data["Atomic Weight"].str.replace(
        r"(?<=\d)\(\d+\.?\d*\)", "", regex=True
    )

    # Removing whitespaces and leftover characters from previous cleaning
    data["Atomic Weight"] = data["Atomic Weight"].str.replace(
        r"\s+|\(|_", "", regex=True
    )

    # Convert the atomic weights to numeric values and drop invalid rows
    data["Atomic Weight"] = pd.to_numeric(data["Atomic Weight"], errors="coerce")
    data.dropna(subset=["Atomic Weight"], inplace=True)

    return data


def create_sqlite_database(data: pd.DataFrame) -> bool:
    """
    Creates a SQLite database and stores the atomic data.

    Args:
        data (pandas.DataFrame): The cleaned atomic data to be stored.

    The database contains a table named "elements" with the following columns:
        - atomic_number (INTEGER): The atomic number of the element (primary key).
        - symbol (TEXT): The chemical symbol of the element.
        - name (TEXT): The name of the element.
        - atomic_weight (REAL): The atomic weight of the element.

    Returns:
    bool: True if database was created, False if it already exists.
    """
    db_path = "elements.db"

    # Check if database exists and has data
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM elements")
            count = cursor.fetchone()[0]
            conn.close()

            if count > 0:
                print(f"Database {db_path} already exists and contains data.")
                return False

        except sqlite3.OperationalError:
            pass

    # Create SQLite database
    print("Creating SQLite database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS elements (
        atomic_number INTEGER PRIMARY KEY,
        symbol TEXT NOT NULL,
        name TEXT NOT NULL,
        atomic_weight REAL
    )
    """)
    conn.commit()

    # Insert data into the elements table
    for index, row in data.iterrows():
        cursor.execute(
            """
        INSERT OR REPLACE INTO elements (atomic_number, symbol, name, atomic_weight)
        VALUES (?, ?, ?, ?)
        """,
            (index, row["Symbol"], row["Element Name"], row["Atomic Weight"]),
        )

    conn.commit()
    conn.close()
    return True


def get_atomic_weights(element_names: List[str]) -> List[float] | None:
    """
    Retrieves the atomic weights for the given element names.

    Args:
        element_names (list): List of element names.

    Returns:
        list: List of atomic weights corresponding to the element names.
    """
    if not element_names:
        raise ValueError("Element names list cannot be empty.")
    try:
        conn = sqlite3.connect("data/elements.db")
        cursor = conn.cursor()
        atomic_weights = []

        for element in element_names:
            cursor.execute("""
            SELECT atomic_weight FROM elements WHERE symbol=?;""", (element,))
            result = cursor.fetchone()
            atomic_weights.append(result[0] if result else None)

        return atomic_weights
    except sqlite3.Error as e:
        raise InputGenerationError(f"Database error: {str(e)}")

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    """
    Main script execution.

    Fetches atomic data from the IUPAC website, processes it, and stores it in a SQLite database.
    """
    url = "https://iupac.qmul.ac.uk/AtWt/"
    html_data = fetch_elements_data(url)
    elements_data = process_elements_data(html_data)
    success = create_sqlite_database(elements_data)

    if success:
        print("Data fetched and stored in elements.db successfully.")
        conn = sqlite3.connect("elements.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM elements;
            """)

        rows = cursor.fetchall()

        if rows:
            print(f"Found {len(rows)} elements in the database")

            # Print the first few results
            for i, row in enumerate(rows[:5]):
                print(f"Element {row[0]}: {row[1]} ({row[2]}) - Weight: {row[3]}")

        else:
            print("Query returned no results")

    else:
        print("Database already exists and contains data. No changes made.")
