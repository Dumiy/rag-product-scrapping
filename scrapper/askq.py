import argparse
from rag import query_data_response, keyword_extract


def main_q(question):
    print(query_data_response(question))


def main_k(sentence):
    print(keyword_extract(sentence))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Description of your program")
    parser.add_argument("-q", help="Question to be passed", default=" ")
    parser.add_argument("-k", help="Keywork extraction input", default=" ")
    args = parser.parse_args()
    if args.q == " ":
        assert "No question received"
    if args.q != " ":
        main_q(args.q)
    else:
        main_k(args.k)
