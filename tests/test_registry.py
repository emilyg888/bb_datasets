from datasets.registry import get_dataset_definition, list_datasets


def test_registry_discovers_gold_dataset():
    definition = get_dataset_definition("fraud_gold")
    assert definition.domain == "fraud"
    assert definition.tier == "gold"
    assert definition.has_labels is True
    assert definition.data_path.name == "data.csv"


def test_registry_filters_by_domain_and_tier():
    fraud_gold = list_datasets(domain="fraud", tier="gold")
    assert [dataset.dataset_id for dataset in fraud_gold] == ["fraud_gold"]
