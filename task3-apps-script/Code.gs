const API_URL = 'https://www.cbr-xml-daily.ru/daily_json.js';
const TARGET_CURRENCIES = ['USD', 'EUR', 'CNY'];

function onOpen() {
  const ui = SpreadsheetApp.getUi();

  ui.createMenu('Курсы валют')
    .addItem('Обновить курсы', 'updateCurrencyRates')
    .addToUi();
}

function updateCurrencyRates() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();

  try {
    const response = UrlFetchApp.fetch(API_URL, {
      method: 'get',
      muteHttpExceptions: true,
    });

    const statusCode = response.getResponseCode();

    if (statusCode !== 200) {
      throw new Error(`API вернул статус ${statusCode}`);
    }

    const data = JSON.parse(response.getContentText());

    if (!data.Valute) {
      throw new Error('В ответе API отсутствует раздел Valute');
    }

    const rows = [
      [
        'Код',
        'Название',
        'Номинал',
        'Текущий курс',
        'Предыдущий курс',
        'Изменение',
        'Изменение, %',
        'Дата данных',
      ],
    ];

    TARGET_CURRENCIES.forEach((code) => {
      const currency = data.Valute[code];

      if (!currency) {
        rows.push([code, 'Валюта не найдена', '', '', '', '', '', data.Date || '']);
        return;
      }

      const currentValue = currency.Value;
      const previousValue = currency.Previous;
      const difference = currentValue - previousValue;
      const percentChange = (difference / previousValue) * 100;

      rows.push([
        code,
        currency.Name,
        currency.Nominal,
        currentValue,
        previousValue,
        Number(difference.toFixed(4)),
        Number(percentChange.toFixed(4)),
        data.Date,
      ]);
    });

    sheet.clearContents();
    sheet.getRange(1, 1, rows.length, rows[0].length).setValues(rows);

    sheet.getRange('J1').setValue('Статус');
    sheet.getRange('J2').setValue(`Успешно обновлено: ${new Date().toLocaleString()}`);

  } catch (error) {
    sheet.getRange('J1').setValue('Статус');
    sheet.getRange('J2').setValue(`Ошибка: ${error.message}`);
  }
}