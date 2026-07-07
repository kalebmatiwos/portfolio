import csv


def extract_data(file_path):
    fieldnames = [
        'timestamp',
        'location',
        'customer name',
        'items ordered',
        'total amount',
        'payment method',
        'card number',
    ]
    data = []
    with open(file_path, mode='r', encoding='utf-8', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if not row:
                continue
            if row[0].startswith('\ufeff'):
                row[0] = row[0].lstrip('\ufeff')
            if len(row) < len(fieldnames):
                continue
            data.append(dict(zip(fieldnames, row)))
    return data


def get_data(data=None):
    if data is None:
        data = extract_data("leeds_28-03-2025.csv")
    return data


def print_data_table(data):
    if not data:
        print('No data to display.')
        return

    headers = [
        'timestamp',
        'location',
        'customer name',
        'items ordered',
        'total amount',
        'payment method',
        'card number',
    ]

    print(' | '.join(headers))
    print('-' * 120)
    for row in data:
        print(' | '.join(str(row.get(key, '')) for key in headers))


if __name__ == '__main__':
    data = get_data()
    print_data_table(data)
