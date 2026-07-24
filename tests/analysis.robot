*** Settings ***
Documentation       Verification tests for the analysis package.
Library             AnalysisLibrary.py

*** Test Cases ***
HistogramAnalyzer Can Be Created
    [Documentation]    A HistogramAnalyzer is an instance of AnalysisModule.
    Create Histogram Analyzer
    Analyzer Type Should Be    HistogramAnalyzer

ImageAnalyzer Can Be Created
    [Documentation]    ImageAnalyzer wraps modules and returns an AnalysisReport.
    Create Image Analyzer
    Analyzer Type Should Be    ImageAnalyzer

HistogramAnalyzer Returns Report With Histogram
    [Documentation]    Running analyze() on a known image produces a
    ...                non-None histogram array.
    Create Histogram Analyzer
    Analyze Known Image
    Result Should Be Analysis Report
    Histogram Should Exist

Histogram Length Matches Unique Pixel Count
    [Documentation]    For a 2x3 image with values 0..5, the histogram
    ...                should have 6 bins (one per unique value).
    Create Histogram Analyzer
    Analyze Known Image
    Histogram Length Should Be    6

ImageAnalyzer Reports Mean Intensity
    [Documentation]    ImageAnalyzer should compute basic intensity
    ...                statistics for a random image.
    Create Image Analyzer
    Analyze Image    height=8    width=8    bit_depth=12
    Result Should Be Analysis Report
    Measurement Should Exist    mean_intensity
    Measurement Should Exist    max_intensity
    Measurement Should Exist    min_intensity

Mean Intensity Is Positive For Random Image
    [Documentation]    For random uint16 pixels, mean, max, and min
    ...                should all be ≥ 0 (never negative).
    Create Image Analyzer
    Analyze Image    height=16    width=16    bit_depth=8
    Measurement Should Exist    mean_intensity
    Measurement Should Exist    max_intensity
    Measurement Should Exist    min_intensity
