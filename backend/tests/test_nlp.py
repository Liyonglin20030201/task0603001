from app.services.nlp_service import generate_summary, extract_tags


CHINESE_TEXT = """
人工智能是计算机科学的一个分支，它企图了解智能的实质。
并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。
人工智能从诞生以来，理论和技术日益成熟，应用领域也不断扩大。
可以设想，未来人工智能带来的科技产品，将会是人类智慧的容器。
人工智能可以对人的意识、思维的信息过程的模拟。
人工智能不是人的智能，但能像人那样思考、也可能超过人的智能。
"""

ENGLISH_TEXT = """
Machine learning is a subset of artificial intelligence.
It focuses on the development of algorithms that can learn from data.
Deep learning is a type of machine learning based on neural networks.
These networks have multiple layers that process information.
The field has seen tremendous growth in recent years.
Applications include image recognition, natural language processing, and robotics.
"""


def test_generate_summary_chinese():
    summary = generate_summary(CHINESE_TEXT, num_sentences=3)
    assert len(summary) > 0
    assert len(summary) < len(CHINESE_TEXT)


def test_generate_summary_english():
    summary = generate_summary(ENGLISH_TEXT, num_sentences=3)
    assert len(summary) > 0
    assert len(summary) < len(ENGLISH_TEXT)


def test_extract_tags():
    tags = extract_tags(CHINESE_TEXT, top_k=5)
    assert isinstance(tags, list)
    assert len(tags) <= 5
    assert len(tags) > 0


def test_short_text_summary():
    short = "This is short."
    summary = generate_summary(short, num_sentences=5)
    assert summary == short or summary == ""
