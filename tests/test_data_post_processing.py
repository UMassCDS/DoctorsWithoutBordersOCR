import pytest
import pandas as pd

from msfocr.data import post_processing

        
def test_evaluate_cells():
    """
    Tests if evaluate_cells works correctly
    """
    df = pd.DataFrame({
        0: ["", "Row 1", "Row 2"],
        1: ["Column 1", "", "-"],
        2: ["Column 2", "", "15"],
        3: ["Column 3", "12+8", "16 - 4"]
    })
    
    answer = pd.DataFrame({
        0: ["", "Row 1", "Row 2"],
        1: ["Column 1", "", "-"],
        2: ["Column 2", "", "15"],
        3: ["Column 3", "20", "12"]
    })
    
    assert post_processing.evaluate_cells([df])[0].equals(answer)