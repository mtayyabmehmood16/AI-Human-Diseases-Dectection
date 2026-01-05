from src.matcher import DiseaseMatcher


def test_find_exact_and_partial():
    m = DiseaseMatcher()
    m.fit_from_csv('data/diseases.csv')
    # exact name present in the dataset
    exact = m.find_by_name('Common Cold', exact=True)
    assert len(exact) >= 1
    assert any('common cold' in d.lower() for d, _, _ in exact)

    # partial search
    partial = m.find_by_name('cold', exact=False)
    assert len(partial) >= 1
    assert any('cold' in d.lower() for d, _, _ in partial)
