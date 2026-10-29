# المؤشرات والأخطاء

**[تجد كل شيفرة هذا الفصل هنا](https://github.com/quii/learn-go-with-tests/tree/main/pointers)**

تعلّمنا في القسم السابق عن البنى (structs)، التي تتيح لنا جمع عدد من القيم المترابطة حول مفهوم واحد.

قد ترغب في مرحلة ما في استعمال البنى لإدارة الحالة، مع إتاحة طرق (methods) تسمح للمستخدمين بتغيير الحالة بطريقة يمكنك التحكم بها.

**قطاع التقنية المالية يحب غو (Go)**، و... أممم، عملات البيتكوين؟ لذا لنُرِ مدى روعة النظام المصرفي الذي يمكننا صنعه.

لننشئ بنية باسم `Wallet` تتيح لنا إيداع `Bitcoin`.

## اكتب الاختبار أولاً

```go
func TestWallet(t *testing.T) {

	wallet := Wallet{}

	wallet.Deposit(10)

	got := wallet.Balance()
	want := 10

	if got != want {
		t.Errorf("got %d want %d", got, want)
	}
}
```

في [المثال السابق](./structs-methods-and-interfaces.md) وصلنا إلى الحقول مباشرة باسم الحقل، لكننا في _محفظتنا الآمنة جداً_ لا نريد أن نكشف حالتنا الداخلية لبقية العالم، بل نريد التحكم بالوصول عبر الطرق.

## حاول تشغيل الاختبار

`./wallet_test.go:7:12: undefined: Wallet`

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

لا يعرف المصرِّف (compiler) ما هي `Wallet`، فلنخبره.

```go
type Wallet struct{}
```

والآن بعد أن أنشأنا محفظتنا، حاول تشغيل الاختبار (test) مجدداً

```
./wallet_test.go:9:8: wallet.Deposit undefined (type Wallet has no field or method Deposit)
./wallet_test.go:11:15: wallet.Balance undefined (type Wallet has no field or method Balance)
```

علينا تعريف هذه الطرق.

تذكّر ألا تفعل إلا ما يكفي لتشغيل الاختبارات. فعلينا التأكد من أن اختبارنا يفشل بشكل صحيح مع رسالة خطأ (error) واضحة.

```go
func (w Wallet) Deposit(amount int) {

}

func (w Wallet) Balance() int {
	return 0
}
```

إن لم تكن هذه الصياغة مألوفة لك، فارجع واقرأ قسم البنى.

ينبغي أن تُصرَّف الاختبارات الآن وتعمل

`wallet_test.go:15: got 0 want 10`

## اكتب ما يكفي من الشيفرة لينجح الاختبار

سنحتاج إلى متغير (variable) ما لـ_الرصيد_ في بنيتنا (struct) لتخزين الحالة

```go
type Wallet struct {
	balance int
}
```

في غو، إن بدأ اسم رمز ما (متغيرات، أنواع، دوال وغيرها) بحرف صغير، فإنه يكون خاصاً _خارج الحزمة التي عُرّف فيها_.

وفي حالتنا نريد أن تستطيع طرقنا التعامل مع هذه القيمة، دون أي أحد آخر.

تذكّر أننا نستطيع الوصول إلى الحقل الداخلي `balance` في البنية باستعمال متغير "المستقبِل".

```go
func (w Wallet) Deposit(amount int) {
	w.balance += amount
}

func (w Wallet) Balance() int {
	return w.balance
}
```

وبعد أن ضمنّا مسيرتنا المهنية في التقنية المالية، شغّل مجموعة الاختبارات واستمتع بالاختبار الناجح

`wallet_test.go:15: got 0 want 10`

### هذا ليس صحيحاً تماماً

حسناً، هذا محيّر، فشيفرتنا (code) تبدو وكأنها يجب أن تعمل.
نضيف المبلغ الجديد إلى رصيدنا، ثم ينبغي أن تعيد طريقة الرصيد حالته الحالية.

في غو، **حين تستدعي دالة أو طريقة فإن الوسطاء** _**تُنسخ**_.

عند استدعاء `func (w Wallet) Deposit(amount int)` يكون `w` نسخة من القيمة التي استدعينا عليها الطريقة.

ودون الخوض كثيراً في علوم الحاسوب، حين تنشئ قيمة، كمحفظة مثلاً، فإنها تُخزَّن في مكان ما في الذاكرة. ويمكنك معرفة _عنوان_ ذلك الجزء من الذاكرة بكتابة `&myVal`.

جرّب بإضافة بعض أوامر الطباعة إلى شيفرتك

```go
func TestWallet(t *testing.T) {

	wallet := Wallet{}

	wallet.Deposit(10)

	got := wallet.Balance()

	fmt.Printf("address of balance in test is %p \n", &wallet.balance)

	want := 10

	if got != want {
		t.Errorf("got %d want %d", got, want)
	}
}
```

```go
func (w Wallet) Deposit(amount int) {
	fmt.Printf("address of balance in Deposit is %p \n", &w.balance)
	w.balance += amount
}
```

يطبع العنصر النائب `%p` عناوين الذاكرة بالنظام الست عشري مع البادئة `0x`، ويطبع محرف الهروب `\n` سطراً جديداً.
لاحظ أننا نحصل على المؤشر (pointer)، أي عنوان الذاكرة، لشيء ما بوضع المحرف `&` في بداية اسم الرمز.

أعد الآن تشغيل الاختبار

```text
address of balance in Deposit is 0xc420012268
address of balance in test is 0xc420012260
```

يمكنك أن ترى أن عنواني الرصيدين مختلفان. فحين نغيّر قيمة الرصيد داخل الشيفرة، فإننا نعمل على نسخة مما جاء من الاختبار، ولذلك يبقى الرصيد في الاختبار دون تغيير.

يمكننا إصلاح ذلك بـ_المؤشرات_. [فالمؤشرات](https://gobyexample.com/pointers) تتيح لنا أن _نشير_ إلى قيم ما ثم نغيّرها.
لذا بدلاً من أخذ نسخة من المحفظة كلها، نأخذ مؤشراً إلى تلك المحفظة كي نستطيع تغيير القيم الأصلية داخلها.

```go
func (w *Wallet) Deposit(amount int) {
	w.balance += amount
}

func (w *Wallet) Balance() int {
	return w.balance
}
```

الفرق أن نوع المستقبِل صار `*Wallet` بدلاً من `Wallet`، ويمكنك قراءته "مؤشر إلى محفظة".

حاول إعادة تشغيل الاختبارات، وينبغي أن تنجح.

قد تتساءل الآن: لماذا نجحت؟ فنحن لم نُلغِ الإشارة في الدالة، أي لم نكتب:

```go
func (w *Wallet) Balance() int {
	return (*w).balance
}
```

بل بدا أننا نتعامل مع الكائن مباشرة. والحقيقة أن الشيفرة أعلاه التي تستعمل `(*w)` صحيحة تماماً. لكن صانعي غو رأوا أن هذه الكتابة مرهقة، لذا تسمح لنا اللغة بكتابة `w.balance` دون إلغاء إشارة صريح.
بل إن لهذه المؤشرات إلى البنى اسماً خاصاً بها: _مؤشرات البنى_، وهي [تُلغى إشارتها تلقائياً](https://golang.org/ref/spec#Method_values).

من الناحية التقنية لا تحتاج إلى تغيير `Balance` لتستعمل مستقبِلاً مؤشراً، فأخذ نسخة من الرصيد لا بأس به. لكن العرف يقضي بأن تُبقي أنواع مستقبِلات طرقك متماثلة حفاظاً على الاتساق.

## أعد الهيكلة

قلنا إننا نصنع محفظة بيتكوين، لكننا لم نذكرها حتى الآن. كنا نستعمل `int` لأنه نوع (type) جيد لعدّ الأشياء!

يبدو إنشاء `struct` لهذا الغرض مبالغة بعض الشيء. فالنوع `int` جيد من حيث طريقة عمله، لكنه ليس وصفياً.

تتيح لك غو إنشاء أنواع جديدة من أنواع موجودة.

والصياغة هي `type MyName OriginalType`

```go
type Bitcoin int

type Wallet struct {
	balance Bitcoin
}

func (w *Wallet) Deposit(amount Bitcoin) {
	w.balance += amount
}

func (w *Wallet) Balance() Bitcoin {
	return w.balance
}
```

```go
func TestWallet(t *testing.T) {

	wallet := Wallet{}

	wallet.Deposit(Bitcoin(10))

	got := wallet.Balance()

	want := Bitcoin(10)

	if got != want {
		t.Errorf("got %d want %d", got, want)
	}
}
```

لإنشاء قيمة من النوع `Bitcoin` استعمل الصياغة `Bitcoin(999)` فحسب.

بفعلنا هذا ننشئ نوعاً جديداً، ويمكننا التصريح عن _طرق_ عليه. وقد يكون هذا مفيداً جداً حين تريد إضافة وظائف خاصة بالمجال فوق أنواع موجودة.

لنحقق الواجهة [Stringer](https://golang.org/pkg/fmt/#Stringer) على النوع `Bitcoin`

```go
type Stringer interface {
	String() string
}
```

هذه الواجهة (interface) معرّفة في الحزمة (package) `fmt`، وتتيح لك تحديد طريقة طباعة نوعك حين يُستعمل مع سلسلة التنسيق `%s` في أوامر الطباعة.

```go
func (b Bitcoin) String() string {
	return fmt.Sprintf("%d BTC", b)
}
```

كما ترى، صياغة إنشاء طريقة على نوع مصرّح عنه هي نفسها صياغة إنشائها على بنية.

بعد ذلك علينا تحديث سلاسل التنسيق في اختبارنا لتستعمل `String()` بدلاً من ذلك.

```go
	if got != want {
		t.Errorf("got %s want %s", got, want)
	}
```

لترى هذا عملياً، أفشل الاختبار عمداً كي نراه

`wallet_test.go:18: got 10 BTC want 20 BTC`

وهذا يوضح ما يجري في اختبارنا.

المتطلب التالي هو دالة `Withdraw`.

## اكتب الاختبار أولاً

إنها تقريباً عكس `Deposit()`

```go
func TestWallet(t *testing.T) {

	t.Run("deposit", func(t *testing.T) {
		wallet := Wallet{}

		wallet.Deposit(Bitcoin(10))

		got := wallet.Balance()

		want := Bitcoin(10)

		if got != want {
			t.Errorf("got %s want %s", got, want)
		}
	})

	t.Run("withdraw", func(t *testing.T) {
		wallet := Wallet{balance: Bitcoin(20)}

		wallet.Withdraw(Bitcoin(10))

		got := wallet.Balance()

		want := Bitcoin(10)

		if got != want {
			t.Errorf("got %s want %s", got, want)
		}
	})
}
```

## حاول تشغيل الاختبار

`./wallet_test.go:26:9: wallet.Withdraw undefined (type Wallet has no field or method Withdraw)`

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

```go
func (w *Wallet) Withdraw(amount Bitcoin) {

}
```

`wallet_test.go:33: got 20 BTC want 10 BTC`

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func (w *Wallet) Withdraw(amount Bitcoin) {
	w.balance -= amount
}
```

## أعد الهيكلة

في اختباراتنا شيء من الازدواجية، فلنُزِلها بإعادة الهيكلة.

```go
func TestWallet(t *testing.T) {

	assertBalance := func(t testing.TB, wallet Wallet, want Bitcoin) {
		t.Helper()
		got := wallet.Balance()

		if got != want {
			t.Errorf("got %s want %s", got, want)
		}
	}

	t.Run("deposit", func(t *testing.T) {
		wallet := Wallet{}
		wallet.Deposit(Bitcoin(10))
		assertBalance(t, wallet, Bitcoin(10))
	})

	t.Run("withdraw", func(t *testing.T) {
		wallet := Wallet{balance: Bitcoin(20)}
		wallet.Withdraw(Bitcoin(10))
		assertBalance(t, wallet, Bitcoin(10))
	})

}
```

ماذا ينبغي أن يحدث إن حاولت سحب مبلغ بالطريقة `Withdraw` أكبر مما بقي في الحساب؟ متطلبنا الآن هو أن نفترض عدم وجود تسهيلات للسحب على المكشوف.

كيف نشير إلى وجود مشكلة عند استعمال `Withdraw`؟

في غو، إن أردت الإشارة إلى خطأ، فالأسلوب المعتاد في اللغة أن تعيد دالتك قيمة `err` كي يتحقق منها المستدعي ويتصرف بناءً عليها.

لنجرّب هذا في اختبار.

## اكتب الاختبار أولاً

```go
t.Run("withdraw insufficient funds", func(t *testing.T) {
	startingBalance := Bitcoin(20)
	wallet := Wallet{startingBalance}
	err := wallet.Withdraw(Bitcoin(100))

	assertBalance(t, wallet, startingBalance)

	if err == nil {
		t.Error("wanted an error but didn't get one")
	}
})
```

نريد أن تعيد `Withdraw` خطأً _إن_ حاولت سحب أكثر مما لديك، وأن يبقى الرصيد كما هو.

ثم نتحقق من أن خطأً قد أُعيد بإفشال الاختبار إن كان `nil`.

القيمة `nil` مرادفة لـ`null` في لغات البرمجة الأخرى. ويمكن أن تكون الأخطاء `nil` لأن نوع القيمة المعادة من `Withdraw` سيكون `error`، وهو واجهة. فإن رأيت دالة تأخذ وسطاء أو تعيد قيماً من أنواع واجهات، فيمكن أن تكون قيمها `nil`.

وكما في `null`، إن حاولت الوصول إلى قيمة هي `nil` فسيُطلَق **ذعر في وقت التشغيل** (runtime panic). وهذا سيئ! ينبغي أن تتأكد من التحقق من قيم `nil`.

## حاول تشغيل الاختبار

`./wallet_test.go:31:25: wallet.Withdraw(Bitcoin(100)) used as value`

لعل الصياغة غير واضحة بعض الشيء، لكن قصدنا السابق من `Withdraw` كان مجرد استدعائها، فهي لا تعيد أي قيمة. ولكي يتم التصريف، علينا تغييرها بحيث يكون لها نوع قيمة معادة.

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

```go
func (w *Wallet) Withdraw(amount Bitcoin) error {
	w.balance -= amount
	return nil
}
```

مرة أخرى، من المهم جداً ألا تكتب إلا ما يكفي من الشيفرة لإرضاء المصرِّف. نصحح الطريقة `Withdraw` لتعيد `error`، وعلينا الآن أن نعيد _شيئاً ما_، فلنُعِد `nil` فحسب.

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func (w *Wallet) Withdraw(amount Bitcoin) error {

	if amount > w.balance {
		return errors.New("oh no")
	}

	w.balance -= amount
	return nil
}
```

تذكّر أن تستورد الحزمة `errors` في شيفرتك.

تنشئ الدالة `errors.New` قيمة `error` جديدة برسالة من اختيارك.

## أعد الهيكلة

لنكتب دالة مساعدة سريعة للاختبار تتحقق من الخطأ، لتحسين قابلية قراءة الاختبار

```go
assertError := func(t testing.TB, err error) {
	t.Helper()
	if err == nil {
		t.Error("wanted an error but didn't get one")
	}
}
```

وفي اختبارنا

```go
t.Run("withdraw insufficient funds", func(t *testing.T) {
	startingBalance := Bitcoin(20)
	wallet := Wallet{startingBalance}
	err := wallet.Withdraw(Bitcoin(100))

	assertError(t, err)
	assertBalance(t, wallet, startingBalance)
})
```

أرجو أنك حين أعدنا خطأً نصه "oh no" كنت تفكر أننا _قد_ نحسّنه لاحقاً، لأنه لا يبدو مفيداً جداً.

وبافتراض أن الخطأ سيصل في النهاية إلى المستخدم، لنحدّث اختبارنا ليؤكد على رسالة خطأ معيّنة بدلاً من مجرد وجود خطأ.

## اكتب الاختبار أولاً

حدّث دالتنا المساعدة لتأخذ قيمة `string` تقارن بها.

```go
assertError := func(t testing.TB, got error, want string) {
	t.Helper()

	if got == nil {
		t.Fatal("didn't get an error but wanted one")
	}

	if got.Error() != want {
		t.Errorf("got %q, want %q", got, want)
	}
}
```

كما ترى، يمكن تحويل قيم `Error` إلى سلسلة نصية بالطريقة `.Error()`، وهذا ما نفعله لمقارنتها بالسلسلة التي نريدها. ونتأكد أيضاً من أن الخطأ ليس `nil` كي لا نستدعي `.Error()` على `nil`.

ثم حدّث موضع الاستدعاء

```go
t.Run("withdraw insufficient funds", func(t *testing.T) {
	startingBalance := Bitcoin(20)
	wallet := Wallet{startingBalance}
	err := wallet.Withdraw(Bitcoin(100))

	assertError(t, err, "cannot withdraw, insufficient funds")
	assertBalance(t, wallet, startingBalance)
})
```

قدّمنا `t.Fatal` التي توقف الاختبار إن استُدعيت. وذلك لأننا لا نريد إجراء أي توكيدات (assertions) أخرى على الخطأ المعاد إن لم يكن هناك خطأ أصلاً. ولولا ذلك لاستمر الاختبار إلى الخطوة التالية ولأطلق الذعر بسبب مؤشر `nil`.

## حاول تشغيل الاختبار

`wallet_test.go:61: got err 'oh no' want 'cannot withdraw, insufficient funds'`

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func (w *Wallet) Withdraw(amount Bitcoin) error {

	if amount > w.balance {
		return errors.New("cannot withdraw, insufficient funds")
	}

	w.balance -= amount
	return nil
}
```

## أعد الهيكلة

لدينا ازدواجية في رسالة الخطأ بين شيفرة الاختبار وشيفرة `Withdraw`.

سيكون مزعجاً حقاً أن يفشل الاختبار إن أراد أحدهم إعادة صياغة الخطأ، فهذا قدر زائد من التفاصيل على اختبارنا. لا يهمنا _حقاً_ ما الصياغة الدقيقة، بل أن يُعاد خطأ ذو معنى يتعلق بالسحب عند تحقق شرط معيّن.

الأخطاء في غو قيم، لذا يمكننا نقلها إلى متغير بإعادة الهيكلة، فيكون لها مصدر حقيقة واحد.

```go
var ErrInsufficientFunds = errors.New("cannot withdraw, insufficient funds")

func (w *Wallet) Withdraw(amount Bitcoin) error {

	if amount > w.balance {
		return ErrInsufficientFunds
	}

	w.balance -= amount
	return nil
}
```

تتيح لنا الكلمة المحجوزة `var` تعريف قيم عامة على مستوى الحزمة.

وهذا تغيير إيجابي في حد ذاته، لأن الدالة `Withdraw` صارت تبدو واضحة جداً.

بعد ذلك يمكننا إعادة هيكلة شيفرة الاختبار لتستعمل هذه القيمة بدلاً من سلاسل نصية محددة.

```go
func TestWallet(t *testing.T) {

	t.Run("deposit", func(t *testing.T) {
		wallet := Wallet{}
		wallet.Deposit(Bitcoin(10))
		assertBalance(t, wallet, Bitcoin(10))
	})

	t.Run("withdraw with funds", func(t *testing.T) {
		wallet := Wallet{Bitcoin(20)}
		wallet.Withdraw(Bitcoin(10))
		assertBalance(t, wallet, Bitcoin(10))
	})

	t.Run("withdraw insufficient funds", func(t *testing.T) {
		wallet := Wallet{Bitcoin(20)}
		err := wallet.Withdraw(Bitcoin(100))

		assertError(t, err, ErrInsufficientFunds)
		assertBalance(t, wallet, Bitcoin(20))
	})
}

func assertBalance(t testing.TB, wallet Wallet, want Bitcoin) {
	t.Helper()
	got := wallet.Balance()

	if got != want {
		t.Errorf("got %q want %q", got, want)
	}
}

func assertError(t testing.TB, got, want error) {
	t.Helper()
	if got == nil {
		t.Fatal("didn't get an error but wanted one")
	}

	if got != want {
		t.Errorf("got %q, want %q", got, want)
	}
}
```

وصار الاختبار الآن أسهل في المتابعة أيضاً.

نقلت الدوال المساعدة خارج دالة الاختبار الرئيسية، كي يبدأ من يفتح الملف بقراءة توكيداتنا أولاً، لا بعض الدوال المساعدة.

ومن الخصائص المفيدة الأخرى للاختبارات أنها تساعدنا على فهم الاستعمال _الحقيقي_ لشيفرتنا، فنكتب شيفرة مراعية لمستعمليها. ونرى هنا أن المطور يستطيع ببساطة استدعاء شيفرتنا والتحقق من المساواة مع `ErrInsufficientFunds` والتصرف وفقاً لذلك.

### الأخطاء غير المفحوصة

مع أن مصرِّف غو يساعدك كثيراً، فقد تفوتك أحياناً بعض الأشياء، وقد تكون معالجة الأخطاء صعبة في بعض الأحيان.

هناك سيناريو واحد لم نختبره. ولإيجاده، شغّل ما يلي في الطرفية لتثبيت `errcheck`، وهي واحدة من أدوات تدقيق ساكن كثيرة متاحة لغو.

`go install github.com/kisielk/errcheck@latest`

ثم شغّل `errcheck .` داخل المجلد الذي فيه شيفرتك.

ينبغي أن تحصل على شيء مثل

`wallet_test.go:17:18: wallet.Withdraw(Bitcoin(10))`

ما يخبرنا به هذا أننا لم نتحقق من الخطأ المعاد في ذلك السطر من الشيفرة. وذلك السطر على حاسوبي يقابل سيناريو السحب العادي، لأننا لم نتحقق من أنه حين تنجح `Withdraw` فإن خطأً _لا_ يُعاد.

إليك شيفرة الاختبار النهائية التي تأخذ ذلك في الحسبان.

```go
func TestWallet(t *testing.T) {

	t.Run("deposit", func(t *testing.T) {
		wallet := Wallet{}
		wallet.Deposit(Bitcoin(10))

		assertBalance(t, wallet, Bitcoin(10))
	})

	t.Run("withdraw with funds", func(t *testing.T) {
		wallet := Wallet{Bitcoin(20)}
		err := wallet.Withdraw(Bitcoin(10))

		assertNoError(t, err)
		assertBalance(t, wallet, Bitcoin(10))
	})

	t.Run("withdraw insufficient funds", func(t *testing.T) {
		wallet := Wallet{Bitcoin(20)}
		err := wallet.Withdraw(Bitcoin(100))

		assertError(t, err, ErrInsufficientFunds)
		assertBalance(t, wallet, Bitcoin(20))
	})
}

func assertBalance(t testing.TB, wallet Wallet, want Bitcoin) {
	t.Helper()
	got := wallet.Balance()

	if got != want {
		t.Errorf("got %s want %s", got, want)
	}
}

func assertNoError(t testing.TB, got error) {
	t.Helper()
	if got != nil {
		t.Fatal("got an error but didn't want one")
	}
}

func assertError(t testing.TB, got error, want error) {
	t.Helper()
	if got == nil {
		t.Fatal("didn't get an error but wanted one")
	}

	if got != want {
		t.Errorf("got %s, want %s", got, want)
	}
}
```

## الخلاصة

### المؤشرات

* تنسخ غو القيم حين تمررها إلى الدوال أو الطرق، لذا إن كنت تكتب دالة تحتاج إلى تغيير الحالة، فستحتاج إلى أن تأخذ مؤشراً إلى الشيء الذي تريد تغييره.
* كون غو تأخذ نسخة من القيم مفيد في كثير من الأحيان، لكنك أحياناً لن تريد أن ينسخ نظامك شيئاً ما، وعندها تحتاج إلى تمرير مرجع. ومن الأمثلة الإشارة إلى هياكل بيانات كبيرة جداً، أو أشياء لا يلزم منها إلا نسخة واحدة (مثل مجمّعات اتصالات قواعد البيانات).

### القيمة `nil`

* يمكن أن تكون المؤشرات `nil`
* حين تعيد دالة مؤشراً إلى شيء ما، عليك التأكد من التحقق مما إذا كان `nil`، وإلا فقد تُطلق استثناءً في وقت التشغيل، ولن يساعدك المصرِّف هنا.
* مفيدة حين تريد وصف قيمة قد تكون مفقودة

### الأخطاء

* الأخطاء هي الوسيلة للإشارة إلى الفشل عند استدعاء دالة أو طريقة.
* بالإصغاء إلى اختباراتنا استنتجنا أن التحقق من سلسلة نصية داخل خطأ سيؤدي إلى اختبار متقلب. لذا أعدنا هيكلة تنفيذنا ليستعمل قيمة ذات معنى بدلاً من ذلك، فنتجت شيفرة أسهل في الاختبار، واستنتجنا أن هذا سيكون أسهل لمستخدمي واجهتنا البرمجية أيضاً.
* هذه ليست نهاية القصة في معالجة الأخطاء، فيمكنك فعل أشياء أكثر تطوراً، لكن هذه مجرد مقدمة. وستتناول أقسام لاحقة مزيداً من الاستراتيجيات.
* [لا تكتفِ بفحص الأخطاء، بل عالجها بأناقة](https://dave.cheney.net/2016/04/27/dont-just-check-errors-handle-them-gracefully)

### أنشئ أنواعاً جديدة من أنواع موجودة

* مفيد لإضافة معنى خاص بالمجال إلى القيم
* يتيح لك تحقيق الواجهات

المؤشرات والأخطاء جزء كبير من كتابة شيفرة غو، وعليك أن تعتاد عليهما. ولحسن الحظ فإن المصرِّف سيساعدك _عادةً_ إن فعلت شيئاً خاطئاً، فقط خذ وقتك واقرأ الخطأ.
