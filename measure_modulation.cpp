// measure the modulation frequency from its power spectral density (PSD) by doing the following:
// 1. Load the PSD data from a CSV file
// 2. Find the three highest local maxima in the spectrum
// 3. Calculate the frequency difference from the central (highest) peack to the two side peaks
// 4. Return the average of the two frequency differences as the modulation frequency
//
// Build: g++ -std=c++17 -O2 -o measure_modulation measure_modulation.cpp
// Usage: ./measure_modulation file1.csv [file2.csv ...]

#include <algorithm>
#include <cmath>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

struct Spectrum {
    std::vector<double> freq;
    std::vector<double> psd;
};

// Each CSV is headerless with two numeric columns (frequency, PSD) and a trailing comma.
Spectrum load_psd(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open " + path);

    Spectrum s;
    std::string line;
    while (std::getline(in, line)) {
        std::replace(line.begin(), line.end(), ',', ' ');
        std::istringstream ss(line);
        double f, p;
        if (ss >> f >> p) {
            s.freq.push_back(f);
            s.psd.push_back(p);
        }
    }
    if (s.freq.size() < 3) throw std::runtime_error("not enough data in " + path);
    return s;
}

// Indices of the n largest local maxima, sorted by descending PSD.
std::vector<size_t> top_local_maxima(const Spectrum& s, size_t n) {
    std::vector<size_t> peaks;
    for (size_t i = 1; i + 1 < s.psd.size(); ++i) {
        if (s.psd[i] > s.psd[i - 1] && s.psd[i] >= s.psd[i + 1]) peaks.push_back(i);
    }
    std::sort(peaks.begin(), peaks.end(),
              [&](size_t a, size_t b) { return s.psd[a] > s.psd[b]; });
    if (peaks.size() > n) peaks.resize(n);
    return peaks;
}

double modulation_frequency(const Spectrum& s) {
    std::vector<size_t> peaks = top_local_maxima(s, 3);
    if (peaks.size() < 3) throw std::runtime_error("fewer than three local maxima found");

    double f_center = s.freq[peaks[0]];
    double df1 = std::fabs(s.freq[peaks[1]] - f_center);
    double df2 = std::fabs(s.freq[peaks[2]] - f_center);
    return 0.5 * (df1 + df2);
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " file1.csv [file2.csv ...]\n";
        return 1;
    }

    int status = 0;
    for (int i = 1; i < argc; ++i) {
        try {
            Spectrum s = load_psd(argv[i]);
            std::vector<size_t> peaks = top_local_maxima(s, 3);
            double fm = modulation_frequency(s);

            std::cout << argv[i] << ":\n";
            for (size_t p : peaks) {
                std::cout << "  peak at " << s.freq[p] << " Hz, PSD = " << s.psd[p] << "\n";
            }
            std::cout << "  modulation frequency = " << fm << " Hz\n";
        } catch (const std::exception& e) {
            std::cerr << argv[i] << ": " << e.what() << "\n";
            status = 1;
        }
    }
    return status;
}
