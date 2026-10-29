# عودة إلى المصفوفات والشرائح مع الأنواع العامة

**[شيفرة هذا الفصل استكمال لفصل المصفوفات والشرائح، وتجدها هنا](https://github.com/quii/learn-go-with-tests/tree/main/arrays)**

ألقِ نظرة على الدالتين `SumAll` و`SumAllTails` اللتين كتبناهما في فصل [المصفوفات والشرائح](arrays-and-slices.md). وإن لم تكن نسختك لديك، فانسخ الشيفرة (code) من فصل [المصفوفات والشرائح](arrays-and-slices.md) مع الاختبارات.

```go
// Sum calculates the total from a slice of numbers.
func Sum(numbers []int) int {
	var sum int
	for _, number := range numbers {
		sum += number
	}
	return sum
}

// SumAllTails calculates the sums of all but the first number given a collection of slices.
func SumAllTails(numbersToSum ...[]int) []int {
	var sums []int
	for _, numbers := range numbersToSum {
		if len(numbers) == 0 {
			sums = append(sums, 0)
		} else {
			tail := numbers[1:]
			sums = append(sums, Sum(tail))
		}
	}

	return sums
}
```

هل ترى نمطاً متكرراً؟

- أنشئ نوعاً من قيمة النتيجة "الابتدائية".
- مُرّ على المجموعة، مطبقاً نوعاً من العمليات (أو دالة) على النتيجة والعنصر التالي في الشريحة، ومسنداً قيمة جديدة للنتيجة
- أعد النتيجة.

يُتحدث عن هذه الفكرة كثيراً في أوساط البرمجة الوظيفية، وغالباً ما تسمى "الاختزال" (reduce) أو [الطيّ](https://en.wikipedia.org/wiki/Fold_(higher-order_function)).

> في البرمجة الوظيفية، يشير الطيّ (ويسمى أيضاً الاختزال أو التراكم أو التجميع أو الضغط أو الحقن) إلى عائلة من الدوال عالية الرتبة التي تحلل هيكل بيانات عَوْدياً، ومن خلال عملية دمج معطاة تعيد دمج نتائج المعالجة العَوْدية لأجزائه المكونة، فتبني قيمة معادة. وعادةً يُقدَّم الطيّ مع دالة دمج، والعقدة العليا لهيكل بيانات، وربما بعض القيم الافتراضية التي تُستعمل في ظروف معيّنة. ثم يمضي الطيّ في دمج عناصر التسلسل الهرمي لهيكل البيانات، مستعملاً الدالة بطريقة منهجية.

لطالما كانت في غو (Go) دوال عالية الرتبة، ومنذ الإصدار 1.18 صارت فيها أيضاً [الأنواع العامة](./generics.md)، لذا صار ممكناً الآن تعريف بعض هذه الدوال التي يُتحدث عنها في مجالنا الأوسع. ولا فائدة من دفن رأسك في الرمال، فهذا تجريد شائع جداً خارج منظومة غو، وسيكون من المفيد فهمه.

أعرف الآن أن بعضكم يتقزز على الأرجح من هذا.

> يُفترض أن تكون غو بسيطة

**لا تخلط بين السهولة والبساطة**. كتابة الحلقات ونسخ الشيفرة ولصقها أمر سهل، لكنه ليس بالضرورة بسيطاً. ولمزيد عن البسيط مقابل السهل، شاهد [تحفة ريتش هيكي: Simple Made Easy](https://www.youtube.com/watch?v=SxdOUGdseq4).

**لا تخلط بين عدم الألفة والتعقيد**. قد يبدو الطيّ أو الاختزال مخيفاً ونظرياً في البداية، لكنه في الحقيقة ليس إلا تجريداً فوق عملية شائعة جداً: أخذ مجموعة ودمجها في عنصر واحد. وحين تتراجع خطوة إلى الخلف، ستدرك أنك على الأرجح تفعل هذا _كثيراً_.

## إعادة هيكلة عامة

من الأخطاء التي يرتكبها الناس كثيراً مع ميزات اللغة الجديدة اللامعة أنهم يبدؤون باستعمالها دون أن تكون لديهم حالة استعمال ملموسة. فيعتمدون على الحدس والتخمين لتوجيه جهودهم.

لحسن الحظ كتبنا دوالنا "المفيدة" ولدينا اختبارات حولها، لذا نحن أحرار الآن في تجربة الأفكار في مرحلة إعادة الهيكلة من `TDD`، ونعرف أن أي شيء نجربه يُتحقق من قيمته عبر اختبارات الوحدة لدينا.

استعمال الأنواع العامة (generics) كأداة لتبسيط الشيفرة عبر خطوة إعادة الهيكلة أرجح بكثير أن يقودك إلى تحسينات مفيدة، بدلاً من تجريدات سابقة لأوانها.

يمكننا تجربة الأشياء بأمان، وإعادة تشغيل اختباراتنا، فإن أعجبنا التغيير نودعه، وإلا نتراجع عنه فحسب. وحرية التجريب هذه من القيم الكبيرة حقاً لـ`TDD`.

ينبغي أن تكون مألوفاً مع صياغة الأنواع العامة [من الفصل السابق](generics.md)، فحاول كتابة دالة `Reduce` خاصة بك واستعمالها داخل `Sum` و`SumAllTails`.

### تلميحات

إن فكرت في وسطاء دالتك أولاً، فسيعطيك ذلك مجموعة صغيرة جداً من الحلول الصالحة
  - المصفوفة التي تريد اختزالها
  - نوع من دوال الدمج

"الاختزال" نمط موثّق جيداً للغاية، ولا حاجة إلى إعادة اختراع العجلة. [اقرأ صفحة الويكي، وخصوصاً قسم القوائم](https://en.wikipedia.org/wiki/Fold_(higher-order_function))، فهو ينبغي أن ينبّهك إلى وسيط آخر ستحتاج إليه.

> عملياً، من المريح والطبيعي أن تكون هناك قيمة ابتدائية

### محاولتي الأولى لـ`Reduce`

```go
func Reduce[A any](collection []A, f func(A, A) A, initialValue A) A {
	var result = initialValue
	for _, x := range collection {
		result = f(result, x)
	}
	return result
}
```

تجسّد `Reduce` _جوهر_ النمط، فهي دالة (function) تأخذ مجموعة، ودالة مراكِمة، وقيمة ابتدائية، وتعيد قيمة واحدة. ولا تشتيت فوضوياً حول الأنواع الملموسة.

إن كنت تفهم صياغة الأنواع العامة، فلن تجد مشكلة في فهم ما تفعله هذه الدالة. وباستعمال المصطلح المعروف `Reduce`، يفهم المبرمجون القادمون من لغات أخرى القصد أيضاً.

### الاستعمال

```go
// Sum calculates the total from a slice of numbers.
func Sum(numbers []int) int {
	add := func(acc, x int) int { return acc + x }
	return Reduce(numbers, add, 0)
}

// SumAllTails calculates the sums of all but the first number given a collection of slices.
func SumAllTails(numbers ...[]int) []int {
	sumTail := func(acc, x []int) []int {
		if len(x) == 0 {
			return append(acc, 0)
		} else {
			tail := x[1:]
			return append(acc, Sum(tail))
		}
	}

	return Reduce(numbers, sumTail, []int{})
}
```

صارت `Sum` و`SumAllTails` تصفان الآن سلوك حساباتهما بالدالتين المصرّح عنهما في سطريهما الأولين على الترتيب. أما فعل تشغيل الحساب على المجموعة فمجرّد داخل `Reduce`.

## تطبيقات أخرى للاختزال

باستعمال الاختبارات يمكننا التلاعب بدالة الاختزال لنرى مدى قابليتها لإعادة الاستعمال. وقد نسخت دوال التوكيد العامة من الفصل السابق.

```go
func TestReduce(t *testing.T) {
	t.Run("multiplication of all elements", func(t *testing.T) {
		multiply := func(x, y int) int {
			return x * y
		}

		AssertEqual(t, Reduce([]int{1, 2, 3}, multiply, 1), 6)
	})

	t.Run("concatenate strings", func(t *testing.T) {
		concatenate := func(x, y string) string {
			return x + y
		}

		AssertEqual(t, Reduce([]string{"a", "b", "c"}, concatenate, ""), "abc")
	})
}
```

### القيمة الصفرية

في مثال الضرب، نبيّن سبب وجود قيمة افتراضية كوسيط (argument) لـ`Reduce`. فلو اعتمدنا على القيمة الافتراضية في غو للنوع `int`، وهي 0، لضربنا قيمتنا الابتدائية في 0، ثم ما يليها، فلن تحصل أبداً إلا على 0. أما بضبطها على 1، فسيبقى العنصر الأول في الشريحة كما هو، وتُضرب البقية في العناصر التالية.

وإن أردت أن تبدو ذكياً أمام أصدقائك المهووسين، فستسمي هذا [العنصر المحايد](https://en.wikipedia.org/wiki/Identity_element).

> في الرياضيات، العنصر المحايد لعملية ثنائية تعمل على مجموعة هو عنصر من المجموعة يُبقي كل عنصر فيها دون تغيير حين تُطبق العملية.

في الجمع، العنصر المحايد هو 0.

`1 + 0 = 1`

وفي الضرب، هو 1.

`1 * 1 = 1`

## ماذا لو أردنا الاختزال إلى نوع مختلف عن `A`؟

لنفترض أن لدينا قائمة من المعاملات المالية `Transaction`، وأردنا دالة تأخذها مع اسم لحساب الرصيد المصرفي.

لنتبع عملية `TDD`.

## اكتب الاختبار أولاً

```go
func TestBadBank(t *testing.T) {
	transactions := []Transaction{
		{
			From: "Chris",
			To:   "Riya",
			Sum:  100,
		},
		{
			From: "Adil",
			To:   "Chris",
			Sum:  25,
		},
	}

	AssertEqual(t, BalanceFor(transactions, "Riya"), 100)
	AssertEqual(t, BalanceFor(transactions, "Chris"), -75)
	AssertEqual(t, BalanceFor(transactions, "Adil"), -25)
}
```

## حاول تشغيل الاختبار
```
# github.com/quii/learn-go-with-tests/arrays/v8 [github.com/quii/learn-go-with-tests/arrays/v8.test]
./bad_bank_test.go:6:20: undefined: Transaction
./bad_bank_test.go:18:14: undefined: BalanceFor
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

ليست لدينا أنواعنا أو دوالنا بعد، فأضفها لجعل الاختبار يعمل.

```go
type Transaction struct {
	From string
	To   string
	Sum  float64
}

func BalanceFor(transactions []Transaction, name string) float64 {
	return 0.0
}
```

حين تشغّل الاختبار (test) ينبغي أن ترى ما يلي:

```
=== RUN   TestBadBank
    bad_bank_test.go:19: got 0, want 100
    bad_bank_test.go:20: got 0, want -75
    bad_bank_test.go:21: got 0, want -25
--- FAIL: TestBadBank (0.00s)
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

لنكتب الشيفرة أولاً كما لو لم تكن لدينا دالة `Reduce`.

```go
func BalanceFor(transactions []Transaction, name string) float64 {
	var balance float64
	for _, t := range transactions {
		if t.From == name {
			balance -= t.Sum
		}
		if t.To == name {
			balance += t.Sum
		}
	}
	return balance
}
```

## أعد الهيكلة

في هذه المرحلة، التزم بانضباط التحكم بالمصدر وأودع عملك. فلدينا برنامج يعمل، جاهز لمنافسة Monzo وBarclays وغيرهما.

والآن بعد أن أودعنا عملنا، نحن أحرار في التلاعب به وتجربة بعض الأفكار المختلفة في مرحلة إعادة الهيكلة (refactoring). وإحقاقاً للحق، الشيفرة التي لدينا ليست سيئة تماماً، لكن من أجل هذا التمرين أريد أن أعرض الشيفرة نفسها باستعمال `Reduce`.

```go
func BalanceFor(transactions []Transaction, name string) float64 {
	adjustBalance := func(currentBalance float64, t Transaction) float64 {
		if t.From == name {
			return currentBalance - t.Sum
		}
		if t.To == name {
			return currentBalance + t.Sum
		}
		return currentBalance
	}
	return Reduce(transactions, adjustBalance, 0.0)
}
```

لكن هذا لن يُصرَّف.

```
./bad_bank.go:19:35: type func(acc float64, t Transaction) float64 of adjustBalance does not match inferred type func(Transaction, Transaction) Transaction for func(A, A) A
```

السبب أننا نحاول الاختزال إلى نوع _مختلف_ عن نوع المجموعة. يبدو هذا مخيفاً، لكنه في الحقيقة لا يتطلب منا إلا تعديل توقيع نوع `Reduce` ليعمل. فلن نضطر إلى تغيير جسم الدالة، ولن نضطر إلى تغيير أي من مستدعينا الحاليين.

```go
func Reduce[A, B any](collection []A, f func(B, A) B, initialValue B) B {
	var result = initialValue
	for _, x := range collection {
		result = f(result, x)
	}
	return result
}
```

أضفنا قيد نوع ثانياً أتاح لنا تخفيف القيود على `Reduce`. وهذا يتيح للناس اختزال مجموعة من `A` إلى `B` بـ`Reduce`. وفي حالتنا من `Transaction` إلى `float64`.

وهذا يجعل `Reduce` أكثر عمومية وقابلية لإعادة الاستعمال، مع بقائها آمنة الأنواع. وإن حاولت تشغيل الاختبارات مجدداً فينبغي أن تُصرَّف وتنجح.

## توسيع المصرف

للمتعة، أردت تحسين سهولة استعمال شيفرة المصرف. وقد حذفت عملية `TDD` اختصاراً.

```go
func TestBadBank(t *testing.T) {
	var (
		riya  = Account{Name: "Riya", Balance: 100}
		chris = Account{Name: "Chris", Balance: 75}
		adil  = Account{Name: "Adil", Balance: 200}

		transactions = []Transaction{
			NewTransaction(chris, riya, 100),
			NewTransaction(adil, chris, 25),
		}
	)

	newBalanceFor := func(account Account) float64 {
		return NewBalanceFor(account, transactions).Balance
	}

	AssertEqual(t, newBalanceFor(riya), 200)
	AssertEqual(t, newBalanceFor(chris), 0)
	AssertEqual(t, newBalanceFor(adil), 175)
}
```

وإليك الشيفرة المحدّثة

```go
package main

type Transaction struct {
	From string
	To   string
	Sum  float64
}

func NewTransaction(from, to Account, sum float64) Transaction {
	return Transaction{From: from.Name, To: to.Name, Sum: sum}
}

type Account struct {
	Name    string
	Balance float64
}

func NewBalanceFor(account Account, transactions []Transaction) Account {
	return Reduce(
		transactions,
		applyTransaction,
		account,
	)
}

func applyTransaction(a Account, transaction Transaction) Account {
	if transaction.From == a.Name {
		a.Balance -= transaction.Sum
	}
	if transaction.To == a.Name {
		a.Balance += transaction.Sum
	}
	return a
}
```

أشعر أن هذا يبيّن حقاً قوة استعمال مفاهيم مثل `Reduce`. فالدالة `NewBalanceFor` تبدو أكثر _تصريحية_، إذ تصف _ما_ يحدث لا _كيف_. وكثيراً ما نكون حين نقرأ الشيفرة متنقلين بسرعة بين ملفات كثيرة، محاولين فهم _ما_ يحدث لا _كيف_، وهذا الأسلوب في الشيفرة يسهّل ذلك جيداً.

وإن أردت التعمق في التفاصيل فيمكنني ذلك، ويمكنني أن أرى _منطق الأعمال_ في `applyTransaction` دون القلق بشأن الحلقات وتغيير الحالة؛ فـ`Reduce` تتولى ذلك بشكل منفصل.


### الطيّ والاختزال عامّان جداً

الاحتمالات لا نهاية لها™️ مع `Reduce` (أو `Fold`). إنه نمط شائع لسبب وجيه، وليس مقتصراً على الحساب أو دمج السلاسل النصية. جرّب بعض التطبيقات الأخرى.

- لماذا لا تمزج بعض قيم `color.RGBA` في لون واحد؟
- اجمع عدد الأصوات في استطلاع، أو العناصر في سلة تسوق.
- وكل ما يتضمن معالجة قائمة تقريباً.

## البحث

والآن بعد أن صارت في غو الأنواع العامة، وبدمجها مع الدوال عالية الرتبة، يمكننا التخلص من كثير من الشيفرة المتكررة في مشاريعنا، لنساعد أنظمتنا على أن تكون أسهل في الفهم والإدارة.

لم تعد بحاجة إلى كتابة دوال `Find` محددة لكل نوع من المجموعات التي تريد البحث فيها، بل أعد استعمال دالة `Find` أو اكتب واحدة. وإن فهمت الدالة `Reduce` أعلاه، فستكون كتابة دالة `Find` أمراً بسيطاً.

إليك اختباراً

```go
func TestFind(t *testing.T) {
	t.Run("find first even number", func(t *testing.T) {
		numbers := []int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}

		firstEvenNumber, found := Find(numbers, func(x int) bool {
			return x%2 == 0
		})
		AssertTrue(t, found)
		AssertEqual(t, firstEvenNumber, 2)
	})
}
```

وإليك التنفيذ

```go
func Find[A any](items []A, predicate func(A) bool) (value A, found bool) {
	for _, v := range items {
		if predicate(v) {
			return v, true
		}
	}
	return
}
```

مرة أخرى، لأنها تأخذ نوعاً عاماً، يمكننا إعادة استعمالها بطرق كثيرة

```go
type Person struct {
	Name string
}

t.Run("Find the best programmer", func(t *testing.T) {
	people := []Person{
		Person{Name: "Kent Beck"},
		Person{Name: "Martin Fowler"},
		Person{Name: "Chris James"},
	}

	king, found := Find(people, func(p Person) bool {
		return strings.Contains(p.Name, "Chris")
	})

	AssertTrue(t, found)
	AssertEqual(t, king, Person{Name: "Chris James"})
})
```

كما ترى، هذه الشيفرة بلا عيب.

## الخلاصة

حين تُستعمل الدوال عالية الرتبة كهذه بذوق، فإنها تجعل شيفرتك أبسط في القراءة والصيانة، لكن تذكّر القاعدة العامة:

استعمل عملية `TDD` لاستخلاص سلوك حقيقي ومحدد تحتاج إليه فعلاً، ثم في مرحلة إعادة الهيكلة _قد_ تكتشف بعض التجريدات المفيدة التي تساعد على ترتيب الشيفرة.

تمرّن على دمج `TDD` مع عادات جيدة في التحكم بالمصدر. أودع عملك حين ينجح اختبارك، _قبل_ محاولة إعادة الهيكلة. فبهذه الطريقة إن أحدثت فوضى، تستطيع بسهولة العودة إلى حالتك التي تعمل.

### الأسماء مهمة

ابذل جهداً في البحث خارج غو، كي لا تعيد اختراع أنماط موجودة بالفعل ولها اسم راسخ.

تكتب دالة تأخذ مجموعة من `A` وتحولها إلى `B`؟ لا تسمّها `Convert`، فهذه [`Map`](https://en.wikipedia.org/wiki/Map_(higher-order_function)). واستعمال الاسم "الصحيح" لهذه الأشياء سيقلل العبء الذهني على الآخرين، ويجعل البحث عنها في محركات البحث لتعلّم المزيد أسهل.

### ألا يبدو هذا مخالفاً للأسلوب المعتاد في اللغة؟

حاول أن تكون منفتح الذهن.

مع أن أساليب غو المعتادة لن تتغير، ولا ينبغي أن تتغير، تغيراً _جذرياً_ بسبب إطلاق الأنواع العامة، فإن الأساليب المعتادة _ستتغير_ لأن اللغة نفسها تتغير! ولا ينبغي أن تكون هذه نقطة خلافية.

قول

> هذا ليس الأسلوب المعتاد في اللغة

دون أي تفاصيل أخرى ليس كلاماً يمكن البناء عليه أو مفيداً، خصوصاً عند مناقشة ميزات جديدة في اللغة.

ناقش مع زملائك الأنماط وأسلوب الشيفرة بناءً على مزاياها لا على العقائد الجامدة. فما دامت لديك اختبارات جيدة التصميم، فستستطيع دائماً إعادة الهيكلة وتحريك الأشياء كلما فهمت ما يناسبك ويناسب فريقك.

### مصادر

الطيّ مفهوم أساسي حقيقي في علوم الحاسوب. وإليك بعض المصادر المثيرة للاهتمام إن أردت التعمق فيه أكثر
- [ويكيبيديا: Fold](https://en.wikipedia.org/wiki/Fold)
- [درس تعليمي عن عمومية الطيّ وقدرته التعبيرية](http://www.cs.nott.ac.uk/~pszgmh/fold.pdf)
