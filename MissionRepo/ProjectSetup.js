/*    Настраивает проект, добавляя нужные колонки и карточки.
 *
 *    Использование:
 *    - Перейдите в раздел Projects вашего репозитория
 *    - Кликните `Create Project`, укажите имя (например, Mission Workflow), кликните `Create Project`
 *    - Скопируйте содержимое этого файла (кликните Raw -> Ctrl + A -> Ctrl + C)
 *    - Откройте консоль браузера (F12 - Console), вставьте скопированный текст и нажмите Enter
 *    - Дождитесь завершения работы скрипта - на странице появится небольшой поп-ап
 */

let cardData = [
	{
		id: 1,
		name: "Дизайн",
		cards: [
			"### Концепция",
			"### Сюжет:\n**Место действия:** \n**Время:** \n**Стороны:** \n",
			"### Задачи"
		]
	},
	{
		id: 2,
		name: "Разработка",
		cards: [
			"Союзные ассеты",
			"Вражеские ассеты:\n - [ ] Оборонительные позиции\n - [ ] Позиции тяжелого вооружения\n - [ ] Техника\n - [ ] Мины, IED, сигнальные системы",
			"Декорации",
			"Объекты задач",
			"Добавление модулей tSF:\n - [ ] tSF Entities (Zeus, Headless, respawn marker, tSF_ScenarioLogic)\n - [ ] CCP\n - [ ] FARP\n - [ ] Artillery support\n - [ ] Airborne support\n - [ ] Gear logics\n - [ ] DynAI logics",
			"Создание зон DynAI",
			"Маркеры:\n - [ ] Стартовая позиция\n - [ ] Союзные силы\n - [ ] Известные и предполагаемые вражеские силы\n - [ ] Важные для выполнения миссии локации\n - [ ] Позиция артиллерии (Artillery support)\n - [ ] Позиции вертолетов (Airborne support)"
		]
	},
	{
		id: 3,
		name: "Конфигурация",
		cards: [
			"#### Киты:\n Игроков",
			"#### Киты:\n NPC",
			"#### Киты:\n Грузов",
			"#### DynAI:\n Редактирование зон",
			"#### DynAI:\n Конфигурация зон",
			"#### tSF:\n Брифинг",
			"#### tSF:\n Условия миссии",
			"#### tSF:\n Настройка модулей"
		]
	},
	{
		id: 4,
		name: "Пред-релиз",
		cards: [
			"Финализация перед ревью",
			"Исправления после ревью"
		]
	},
	{
		id: 5,
		name: "Релиз",
		cards: [
			"Оформление репозитория",
			"Очистка и запаковка миссии",
			"Заливка миссии на сервер",
			"Проверка миссии на сервере",
			"Добавление информации о миссии в Mission List"
		]
	}
]

let cssLocators = {
	addColBtn: ".btn-primary[data-dialog-id='add-column']",
	addColName: "input#project-column-name-",
	addColConfirm: "form[action$='/columns'] > div > button",
	addCardBtn: ".project-columns .project-column:nth-child($) > div > div > button",
	addCardTextarea: ".project-columns .project-column:nth-child($) textarea",
	addCardConfirm: ".project-columns .project-column:nth-child($) form button",
	addCardCancel: ".project-columns .project-column:nth-child($) form .js-dismiss-note-form-button",
	format: function(line, replaceTo) {
		return line.replace("$", replaceTo)
	},
	get: function (locator, replaceTo) {
		if (replaceTo != null) {
			locator = this.format(locator, replaceTo)
		}
		return document.querySelector(locator);
	},
	click: function (locator, replaceTo) {
		let el = this.get(locator, replaceTo)
		el.removeAttribute("disabled")
		el.click()
	},
	sendKeys: function (locator, replaceTo, keys) {
		let el = this.get(locator, replaceTo)
		el.value = keys;
	}
};

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)) }
async function waitAndAdd(columnInfo) {
	if (addingColumn) {
		setTimeout((columnInfo) => { waitAndAdd(columnInfo) }, 1500, columnInfo);
	} else {
		// Starting with column
		addingColumn = true
		
		// -- Add column
		cssLocators.click(cssLocators.addColBtn);
		await sleep(200)
		cssLocators.sendKeys(cssLocators.addColName,null,columnInfo.name)
		cssLocators.click(cssLocators.addColConfirm)

		// -- Add cards
		await sleep(1000)
		cssLocators.click(cssLocators.addCardBtn, columnInfo.id)
		await sleep(50)
		for (let i = columnInfo.cards.length - 1; i >= 0; --i) {
			cssLocators.sendKeys(cssLocators.addCardTextarea, columnInfo.id, columnInfo.cards[i])
			cssLocators.click(cssLocators.addCardConfirm, columnInfo.id)
			await sleep(1000)
		}
		cssLocators.click(cssLocators.addCardCancel, columnInfo.id)
		// Finished with column
		addingColumn = false
		
		if (++addingColumnsIndex >= cardData.length) {
			alert("Project ready!");
		}
	}
}

var addingColumn = false;
var addingColumnsIndex = 0;
cardData.forEach((x) => { waitAndAdd(x) });
