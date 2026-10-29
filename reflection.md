# الانعكاس

**[تجد كل شيفرة هذا الفصل هنا](https://github.com/quii/learn-go-with-tests/tree/main/reflection)**

[من تويتر](https://twitter.com/peterbourgon/status/1011403901419937792?s=09)

> تحدٍّ في غو: اكتب دالة `walk(x interface{}, fn func(string))` تأخذ بنية `x` وتستدعي `fn` لكل حقول السلاسل النصية الموجودة فيها. مستوى الصعوبة: بشكل عَوْدي.

لفعل هذا سنحتاج إلى استعمال _الانعكاس_ (reflection).

> الانعكاس في الحوسبة هو قدرة البرنامج على فحص بنيته الذاتية، وخصوصاً عبر الأنواع؛ وهو شكل من أشكال البرمجة الوصفية. وهو أيضاً مصدر كبير للحيرة.

من [مدونة غو: الانعكاس](https://blog.golang.org/laws-of-reflection)

## ما هو `interface{}`؟

استمتعنا بأمان الأنواع الذي توفره لنا غو (Go) فيما يخص الدوال (functions) التي تعمل مع أنواع معروفة، مثل `string` و`int` وأنواعنا الخاصة مثل `BankAccount`.

وهذا يعني أننا نحصل على شيء من التوثيق مجاناً، وأن المصرِّف (compiler) سيعترض إن حاولت تمرير نوع خاطئ إلى دالة.

لكنك قد تصادف سيناريوهات تريد فيها كتابة دالة لا تعرف فيها النوع (type) في وقت التصريف.

تتيح لنا غو تجاوز ذلك بالنوع `interface{}`، الذي يمكنك أن تعدّه _أي_ نوع (في الحقيقة، `any` في غو [اسم بديل](https://cs.opensource.google/go/go/+/master:src/builtin/builtin.go;drc=master;l=95) لـ`interface{}`).

لذا فإن `walk(x interface{}, fn func(string))` ستقبل أي قيمة للمعامل `x`.

### فلماذا لا نستعمل `interface{}` لكل شيء ونحصل على دوال مرنة جداً؟

- بصفتك مستخدماً لدالة تأخذ `interface{}`، فإنك تفقد أمان الأنواع. ماذا لو كنت تقصد تمرير `Herd.species` من النوع `string` إلى دالة، لكنك مررت `Herd.count` وهو `int`؟ لن يستطيع المصرِّف إبلاغك بخطئك. كما أنك لا تعرف _ما_ يُسمح لك بتمريره إلى الدالة. فمعرفة أن دالة ما تأخذ `UserService` مثلاً أمر مفيد جداً.
- وبصفتك كاتباً لدالة كهذه، فعليك أن تستطيع فحص _أي شيء_ يُمرَّر إليك، ومحاولة معرفة نوعه وما يمكنك فعله به. ويتم ذلك باستعمال _الانعكاس_. وقد يكون هذا مرتبكاً وصعب القراءة، وهو عموماً أقل كفاءة في الأداء (لأن عليك إجراء الفحوص في وقت التشغيل).

باختصار، لا تستعمل الانعكاس إلا إن كنت تحتاج إليه حقاً.

إن أردت دوال متعددة الأشكال، ففكّر فيما إذا كان بإمكانك تصميمها حول واجهة (interface) (لا `interface{}`، وهذا محيّر)، كي يستطيع المستخدمون استعمال دالتك مع أنواع متعددة إن حققت الطرق (methods) التي تحتاج إليها دالتك لتعمل.

ستحتاج دالتنا إلى أن تعمل مع أشياء كثيرة مختلفة. وكالعادة سنتبع أسلوباً تكرارياً، فنكتب اختبارات لكل شيء جديد نريد دعمه، ونعيد الهيكلة على طول الطريق حتى ننتهي.

## اكتب الاختبار أولاً

سنريد استدعاء دالتنا ببنية (struct) فيها حقل من نوع السلسلة النصية (`x`). ثم يمكننا التجسس على الدالة الممررة (`fn`) لنرى إن كانت تُستدعى.

```go
func TestWalk(t *testing.T) {

	expected := "Chris"
	var got []string

	x := struct {
		Name string
	}{expected}

	walk(x, func(input string) {
		got = append(got, input)
	})

	if len(got) != 1 {
		t.Errorf("wrong number of function calls, got %d want %d", len(got), 1)
	}
}
```

- نريد تخزين شريحة (slice) من السلاسل النصية (`got`) تحفظ السلاسل التي مررتها `walk` إلى `fn`. كثيراً ما أنشأنا في الفصول السابقة أنواعاً مخصصة لهذا الغرض للتجسس على استدعاءات الدوال والطرق، لكننا في هذه الحالة نستطيع ببساطة تمرير دالة مجهولة للمعامل `fn` تُغلِّف `got`.
- نستعمل `struct` مجهولة فيها حقل `Name` من نوع السلسلة النصية لنسلك أبسط مسار "ناجح".
- وأخيراً، نستدعي `walk` مع `x` والجاسوس، ونكتفي الآن بالتحقق من طول `got`. وسنجعل توكيداتنا أكثر تحديداً بعد أن نجعل شيئاً بسيطاً جداً يعمل.

## حاول تشغيل الاختبار

```
./reflection_test.go:21:2: undefined: walk
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

علينا تعريف `walk`

```go
func walk(x interface{}, fn func(input string)) {

}
```

حاول تشغيل الاختبار مجدداً

```
=== RUN   TestWalk
--- FAIL: TestWalk (0.00s)
    reflection_test.go:19: wrong number of function calls, got 0 want 1
FAIL
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

يمكننا استدعاء الجاسوس بأي سلسلة نصية لجعل هذا ينجح.

```go
func walk(x interface{}, fn func(input string)) {
	fn("I still can't believe South Korea beat Germany 2-0 to put them last in their group")
}
```

ينبغي أن ينجح الاختبار (test) الآن. والخطوة التالية هي إجراء توكيد (assertion) أكثر تحديداً على ما تُستدعى به `fn`.

## اكتب الاختبار أولاً

أضف ما يلي إلى الاختبار الحالي للتحقق من أن السلسلة النصية الممررة إلى `fn` صحيحة

```go
if got[0] != expected {
	t.Errorf("got %q, want %q", got[0], expected)
}
```

## حاول تشغيل الاختبار

```
=== RUN   TestWalk
--- FAIL: TestWalk (0.00s)
    reflection_test.go:23: got 'I still can't believe South Korea beat Germany 2-0 to put them last in their group', want 'Chris'
FAIL
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func walk(x interface{}, fn func(input string)) {
	val := reflect.ValueOf(x)
	field := val.Field(0)
	fn(field.String())
}
```

هذه الشيفرة (code) _غير آمنة إطلاقاً وساذجة جداً_، لكن تذكّر أن هدفنا حين نكون في مرحلة "الأحمر" (حين تفشل الاختبارات) هو كتابة أقل قدر ممكن من الشيفرة. ثم نكتب مزيداً من الاختبارات لمعالجة مخاوفنا.

علينا استعمال الانعكاس لإلقاء نظرة على `x` ومحاولة فحص خصائصه.

في [الحزمة reflect](https://pkg.go.dev/reflect) دالة اسمها `ValueOf` تعيد لنا قيمة `Value` لمتغير معيّن. ولهذه القيمة طرق تتيح لنا فحصها، بما في ذلك حقولها التي نستعملها في السطر التالي.

ثم نضع بعض الافتراضات المتفائلة جداً حول القيمة الممررة:

- ننظر إلى الحقل الأول والوحيد. لكن قد لا تكون هناك حقول إطلاقاً، وهذا سيُطلق الذعر.
- ثم نستدعي `String()` التي تعيد القيمة الأساسية كسلسلة نصية. لكن هذا سيكون خاطئاً إن كان الحقل شيئاً آخر غير السلسلة النصية.

## أعد الهيكلة

تنجح شيفرتنا في الحالة البسيطة، لكننا نعرف أن فيها كثيراً من أوجه القصور.

سنكتب عدداً من الاختبارات نمرر فيها قيماً مختلفة، ونتحقق من مصفوفة السلاسل النصية التي استُدعيت بها `fn`.

ينبغي أن نعيد هيكلة اختبارنا إلى اختبار جدولي، ليسهل مواصلة اختبار سيناريوهات جديدة.

```go
func TestWalk(t *testing.T) {

	cases := []struct {
		Name          string
		Input         interface{}
		ExpectedCalls []string
	}{
		{
			"struct with one string field",
			struct {
				Name string
			}{"Chris"},
			[]string{"Chris"},
		},
	}

	for _, test := range cases {
		t.Run(test.Name, func(t *testing.T) {
			var got []string
			walk(test.Input, func(input string) {
				got = append(got, input)
			})

			if !reflect.DeepEqual(got, test.ExpectedCalls) {
				t.Errorf("got %v, want %v", got, test.ExpectedCalls)
			}
		})
	}
}
```

يمكننا الآن بسهولة إضافة سيناريو لنرى ما يحدث إن كان لدينا أكثر من حقل من نوع السلسلة النصية.

## اكتب الاختبار أولاً

أضف السيناريو التالي إلى `cases`.

```
{
    "struct with two string fields",
    struct {
        Name string
        City string
    }{"Chris", "London"},
    []string{"Chris", "London"},
}
```

## حاول تشغيل الاختبار

```
=== RUN   TestWalk/struct_with_two_string_fields
    --- FAIL: TestWalk/struct_with_two_string_fields (0.00s)
        reflection_test.go:40: got [Chris], want [Chris London]
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func walk(x interface{}, fn func(input string)) {
	val := reflect.ValueOf(x)

	for i := 0; i < val.NumField(); i++ {
		field := val.Field(i)
		fn(field.String())
	}
}
```

للقيمة `val` طريقة اسمها `NumField` تعيد عدد الحقول في القيمة. وهذا يتيح لنا المرور على الحقول واستدعاء `fn`، فينجح اختبارنا.

## أعد الهيكلة

لا يبدو أن هناك إعادة هيكلة واضحة هنا تحسّن الشيفرة، فلنمضِ قدماً.

القصور التالي في `walk` أنها تفترض أن كل حقل من النوع `string`. لنكتب اختباراً لهذا السيناريو.

## اكتب الاختبار أولاً

أضف الحالة التالية

```
{
    "struct with non string field",
    struct {
        Name string
        Age  int
    }{"Chris", 33},
    []string{"Chris"},
},
```

## حاول تشغيل الاختبار

```
=== RUN   TestWalk/struct_with_non_string_field
    --- FAIL: TestWalk/struct_with_non_string_field (0.00s)
        reflection_test.go:46: got [Chris <int Value>], want [Chris]
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

علينا التحقق من أن نوع الحقل هو `string`.

```go
func walk(x interface{}, fn func(input string)) {
	val := reflect.ValueOf(x)

	for i := 0; i < val.NumField(); i++ {
		field := val.Field(i)

		if field.Kind() == reflect.String {
			fn(field.String())
		}
	}
}
```

ويمكننا فعل ذلك بالتحقق من [`Kind`](https://pkg.go.dev/reflect#Kind) الخاص به.

## أعد الهيكلة

مرة أخرى، تبدو الشيفرة معقولة بما يكفي في الوقت الحالي.

السيناريو التالي: ماذا لو لم تكن `struct` "مسطحة"؟ بعبارة أخرى، ماذا يحدث إن كانت لدينا `struct` فيها حقول متداخلة؟

## اكتب الاختبار أولاً

كنا نستعمل صياغة البنى المجهولة للتصريح عن أنواع مرتجلة لاختباراتنا، لذا يمكننا مواصلة ذلك هكذا

```
{
    "nested fields",
    struct {
        Name string
        Profile struct {
            Age  int
            City string
        }
    }{"Chris", struct {
        Age  int
        City string
    }{33, "London"}},
    []string{"Chris", "London"},
},
```

لكن يمكننا أن نرى أن الصياغة تصبح فوضوية قليلاً حين تكون هناك بنى مجهولة داخلية. [وهناك اقتراح لجعل الصياغة أجمل](https://github.com/golang/go/issues/12854).

لنُعِد هيكلة هذا ببساطة بإنشاء نوع معروف لهذا السيناريو والإشارة إليه في الاختبار. في هذا شيء من عدم المباشرة، إذ إن بعض شيفرة اختبارنا خارج الاختبار، لكن ينبغي أن يستطيع القراء استنتاج شكل `struct` بالنظر إلى تهيئتها.

أضف تصريحات الأنواع التالية في مكان ما من ملف اختبارك

```go
type Person struct {
	Name    string
	Profile Profile
}

type Profile struct {
	Age  int
	City string
}
```

يمكننا الآن إضافة هذا إلى حالاتنا، وهو أوضح بكثير من قبل

```
{
    "nested fields",
    Person{
        "Chris",
        Profile{33, "London"},
    },
    []string{"Chris", "London"},
},
```

## حاول تشغيل الاختبار

```
=== RUN   TestWalk/Nested_fields
    --- FAIL: TestWalk/nested_fields (0.00s)
        reflection_test.go:54: got [Chris], want [Chris London]
```

المشكلة أننا لا نمر إلا على حقول المستوى الأول من تسلسل النوع الهرمي.

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func walk(x interface{}, fn func(input string)) {
	val := reflect.ValueOf(x)

	for i := 0; i < val.NumField(); i++ {
		field := val.Field(i)

		if field.Kind() == reflect.String {
			fn(field.String())
		}

		if field.Kind() == reflect.Struct {
			walk(field.Interface(), fn)
		}
	}
}
```

الحل بسيط جداً: نفحص `Kind` مرة أخرى، وإن كانت `struct` فإننا نستدعي `walk` مجدداً على تلك `struct` الداخلية.

## أعد الهيكلة

```go
func walk(x interface{}, fn func(input string)) {
	val := reflect.ValueOf(x)

	for i := 0; i < val.NumField(); i++ {
		field := val.Field(i)

		switch field.Kind() {
		case reflect.String:
			fn(field.String())
		case reflect.Struct:
			walk(field.Interface(), fn)
		}
	}
}
```

حين تجري مقارنة على القيمة نفسها أكثر من مرة، فإن إعادة الهيكلة إلى `switch` تحسّن _عموماً_ قابلية القراءة وتجعل شيفرتك أسهل في التوسيع.

ماذا لو كانت قيمة البنية الممررة مؤشراً (pointer)؟

## اكتب الاختبار أولاً

أضف هذه الحالة

```
{
    "pointers to things",
    &Person{
        "Chris",
        Profile{33, "London"},
    },
    []string{"Chris", "London"},
},
```

## حاول تشغيل الاختبار

```
=== RUN   TestWalk/pointers_to_things
panic: reflect: call of reflect.Value.NumField on ptr Value [recovered]
    panic: reflect: call of reflect.Value.NumField on ptr Value
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func walk(x interface{}, fn func(input string)) {
	val := reflect.ValueOf(x)

	if val.Kind() == reflect.Pointer {
		val = val.Elem()
	}

	for i := 0; i < val.NumField(); i++ {
		field := val.Field(i)

		switch field.Kind() {
		case reflect.String:
			fn(field.String())
		case reflect.Struct:
			walk(field.Interface(), fn)
		}
	}
}
```

لا يمكنك استعمال `NumField` على قيمة `Value` هي مؤشر، بل علينا أولاً استخراج القيمة الأساسية باستعمال `Elem()`.

## أعد الهيكلة

لنغلّف مسؤولية استخراج `reflect.Value` من قيمة `interface{}` معيّنة في دالة.

```go
func walk(x interface{}, fn func(input string)) {
	val := getValue(x)

	for i := 0; i < val.NumField(); i++ {
		field := val.Field(i)

		switch field.Kind() {
		case reflect.String:
			fn(field.String())
		case reflect.Struct:
			walk(field.Interface(), fn)
		}
	}
}

func getValue(x interface{}) reflect.Value {
	val := reflect.ValueOf(x)

	if val.Kind() == reflect.Pointer {
		val = val.Elem()
	}

	return val
}
```

هذا يضيف في الحقيقة شيفرة _أكثر_، لكنني أشعر أن مستوى التجريد صحيح.

- احصل على `reflect.Value` للقيمة `x` كي أستطيع فحصها، ولا يهمني كيف.
- مُرّ على الحقول، وافعل ما يلزم بحسب نوع كل منها.

بعد ذلك علينا تغطية الشرائح.

## اكتب الاختبار أولاً

```
{
    "slices",
    []Profile {
        {33, "London"},
        {34, "Reykjavík"},
    },
    []string{"London", "Reykjavík"},
},
```

## حاول تشغيل الاختبار

```
=== RUN   TestWalk/slices
panic: reflect: call of reflect.Value.NumField on slice Value [recovered]
    panic: reflect: call of reflect.Value.NumField on slice Value
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

هذا يشبه سيناريو المؤشر السابق، فنحن نحاول استدعاء `NumField` على `reflect.Value` لكنها لا تملكها لأنها ليست بنية.

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func walk(x interface{}, fn func(input string)) {
	val := getValue(x)

	if val.Kind() == reflect.Slice {
		for i := 0; i < val.Len(); i++ {
			walk(val.Index(i).Interface(), fn)
		}
		return
	}

	for i := 0; i < val.NumField(); i++ {
		field := val.Field(i)

		switch field.Kind() {
		case reflect.String:
			fn(field.String())
		case reflect.Struct:
			walk(field.Interface(), fn)
		}
	}
}
```

## أعد الهيكلة

هذا يعمل لكنه مقزز. لا بأس، فلدينا شيفرة تعمل ومدعومة بالاختبارات، لذا نحن أحرار في العبث بها كما نشاء.

إن فكرت بشيء من التجريد، فإننا نريد استدعاء `walk` إما على

- كل حقل في بنية
- كل _شيء_ في شريحة

شيفرتنا حالياً تفعل هذا، لكنها لا تعكسه جيداً. فلدينا فقط فحص في البداية لنرى إن كانت شريحة (مع `return` لإيقاف تنفيذ بقية الشيفرة)، وإن لم تكن نفترض أنها بنية.

لنُعِد صياغة الشيفرة بحيث نتحقق من النوع _أولاً_ ثم نؤدي عملنا.

```go
func walk(x interface{}, fn func(input string)) {
	val := getValue(x)

	switch val.Kind() {
	case reflect.Struct:
		for i := 0; i < val.NumField(); i++ {
			walk(val.Field(i).Interface(), fn)
		}
	case reflect.Slice:
		for i := 0; i < val.Len(); i++ {
			walk(val.Index(i).Interface(), fn)
		}
	case reflect.String:
		fn(val.String())
	}
}
```

تبدو أفضل بكثير! إن كانت بنية أو شريحة فإننا نمر على قيمها ونستدعي `walk` على كل منها. وإلا، فإن كانت `reflect.String` يمكننا استدعاء `fn`.

ومع ذلك، أشعر أنها يمكن أن تكون أفضل. فهناك تكرار لعملية المرور على الحقول أو القيم ثم استدعاء `walk`، مع أنهما من الناحية المفاهيمية الشيء نفسه.

```go
func walk(x interface{}, fn func(input string)) {
	val := getValue(x)

	numberOfValues := 0
	var getField func(int) reflect.Value

	switch val.Kind() {
	case reflect.String:
		fn(val.String())
	case reflect.Struct:
		numberOfValues = val.NumField()
		getField = val.Field
	case reflect.Slice:
		numberOfValues = val.Len()
		getField = val.Index
	}

	for i := 0; i < numberOfValues; i++ {
		walk(getField(i).Interface(), fn)
	}
}
```

إن كانت `value` من النوع `reflect.String` فإننا نستدعي `fn` كالمعتاد.

وإلا، فستستخرج تعليمة `switch` شيئين بحسب النوع

- عدد الحقول
- طريقة استخراج `Value` (بـ`Field` أو `Index`)

وبعد أن نحدد هذين الأمرين، يمكننا المرور على `numberOfValues` واستدعاء `walk` بنتيجة الدالة `getField`.

والآن بعد أن فعلنا هذا، ينبغي أن تكون معالجة المصفوفات (arrays) أمراً بسيطاً.

## اكتب الاختبار أولاً

أضف إلى الحالات

```
{
    "arrays",
    [2]Profile {
        {33, "London"},
        {34, "Reykjavík"},
    },
    []string{"London", "Reykjavík"},
},
```

## حاول تشغيل الاختبار

```
=== RUN   TestWalk/arrays
    --- FAIL: TestWalk/arrays (0.00s)
        reflection_test.go:78: got [], want [London Reykjavík]
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

يمكن معالجة المصفوفات بالطريقة نفسها التي تُعالج بها الشرائح، لذا أضفها إلى الحالة نفسها بفاصلة فحسب

```go
func walk(x interface{}, fn func(input string)) {
	val := getValue(x)

	numberOfValues := 0
	var getField func(int) reflect.Value

	switch val.Kind() {
	case reflect.String:
		fn(val.String())
	case reflect.Struct:
		numberOfValues = val.NumField()
		getField = val.Field
	case reflect.Slice, reflect.Array:
		numberOfValues = val.Len()
		getField = val.Index
	}

	for i := 0; i < numberOfValues; i++ {
		walk(getField(i).Interface(), fn)
	}
}
```

النوع التالي الذي نريد معالجته هو `map`.

## اكتب الاختبار أولاً

```
{
    "maps",
    map[string]string{
        "Cow": "Moo",
        "Sheep": "Baa",
    },
    []string{"Moo", "Baa"},
},
```

## حاول تشغيل الاختبار

```
=== RUN   TestWalk/maps
    --- FAIL: TestWalk/maps (0.00s)
        reflection_test.go:86: got [], want [Moo Baa]
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

مرة أخرى، إن فكرت بشيء من التجريد فسترى أن `map` تشبه كثيراً `struct`، إلا أن المفاتيح غير معروفة في وقت التصريف.

```go
func walk(x interface{}, fn func(input string)) {
	val := getValue(x)

	numberOfValues := 0
	var getField func(int) reflect.Value

	switch val.Kind() {
	case reflect.String:
		fn(val.String())
	case reflect.Struct:
		numberOfValues = val.NumField()
		getField = val.Field
	case reflect.Slice, reflect.Array:
		numberOfValues = val.Len()
		getField = val.Index
	case reflect.Map:
		for _, key := range val.MapKeys() {
			walk(val.MapIndex(key).Interface(), fn)
		}
	}

	for i := 0; i < numberOfValues; i++ {
		walk(getField(i).Interface(), fn)
	}
}
```

لكن بحكم التصميم لا يمكنك استخراج القيم من خريطة (map) بالفهرس، بل بـ_المفتاح_ فقط، وهذا يكسر تجريدنا، يا للأسف.

## أعد الهيكلة

كيف تشعر الآن؟ بدا الأمر في حينه تجريداً جميلاً ربما، لكن الشيفرة تبدو الآن معوجّة بعض الشيء.

_لا بأس بذلك!_ إعادة الهيكلة (refactoring) رحلة، وسنرتكب أحياناً أخطاء. ومن أهم مزايا `TDD` أنه يمنحنا حرية تجربة هذه الأشياء.

وباتخاذ خطوات صغيرة مدعومة بالاختبارات، فإن هذا ليس وضعاً لا رجعة فيه بأي حال. فلنُعِد الشيفرة ببساطة إلى ما كانت عليه قبل إعادة الهيكلة.

```go
func walk(x interface{}, fn func(input string)) {
	val := getValue(x)

	walkValue := func(value reflect.Value) {
		walk(value.Interface(), fn)
	}

	switch val.Kind() {
	case reflect.String:
		fn(val.String())
	case reflect.Struct:
		for i := 0; i < val.NumField(); i++ {
			walkValue(val.Field(i))
		}
	case reflect.Slice, reflect.Array:
		for i := 0; i < val.Len(); i++ {
			walkValue(val.Index(i))
		}
	case reflect.Map:
		for _, key := range val.MapKeys() {
			walkValue(val.MapIndex(key))
		}
	}
}
```

قدّمنا `walkValue` التي تزيل التكرار في استدعاءات `walk` داخل `switch`، بحيث لا يبقى على كل حالة إلا استخراج قيم `reflect.Value` من `val`.

### مشكلة أخيرة

تذكّر أن الخرائط في غو لا تضمن الترتيب، لذا ستفشل اختباراتك أحياناً لأننا نؤكد أن استدعاءات `fn` تتم بترتيب معيّن.

لإصلاح ذلك، علينا نقل توكيدنا الخاص بالخرائط إلى اختبار جديد لا يهمنا فيه الترتيب.

```go
t.Run("with maps", func(t *testing.T) {
	aMap := map[string]string{
		"Cow":   "Moo",
		"Sheep": "Baa",
	}

	var got []string
	walk(aMap, func(input string) {
		got = append(got, input)
	})

	assertContains(t, got, "Moo")
	assertContains(t, got, "Baa")
})
```

إليك كيف عُرّفت `assertContains`

```go
func assertContains(t testing.TB, haystack []string, needle string) {
	t.Helper()
	contains := false
	for _, x := range haystack {
		if x == needle {
			contains = true
		}
	}
	if !contains {
		t.Errorf("expected %v to contain %q but it didn't", haystack, needle)
	}
}
```

بما أننا نقلنا الخرائط إلى اختبار جديد، فلم نرَ رسالة الفشل. أفشل الاختبار `with maps` هنا عمداً كي تتحقق من رسالة الخطأ، ثم أصلحه مجدداً لتنجح كل الاختبارات.

النوع التالي الذي نريد معالجته هو `chan`.

## اكتب الاختبار أولاً

```go
t.Run("with channels", func(t *testing.T) {
	aChannel := make(chan Profile)

	go func() {
		aChannel <- Profile{33, "Berlin"}
		aChannel <- Profile{34, "Katowice"}
		close(aChannel)
	}()

	var got []string
	want := []string{"Berlin", "Katowice"}

	walk(aChannel, func(input string) {
		got = append(got, input)
	})

	if !reflect.DeepEqual(got, want) {
		t.Errorf("got %v, want %v", got, want)
	}
})
```

## حاول تشغيل الاختبار

```
--- FAIL: TestWalk (0.00s)
    --- FAIL: TestWalk/with_channels (0.00s)
        reflection_test.go:115: got [], want [Berlin Katowice]
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

يمكننا المرور على كل القيم المرسلة عبر القناة (channel) حتى تُغلق، باستعمال `Recv()`

```go
func walk(x interface{}, fn func(input string)) {
	val := getValue(x)

	walkValue := func(value reflect.Value) {
		walk(value.Interface(), fn)
	}

	switch val.Kind() {
	case reflect.String:
		fn(val.String())
	case reflect.Struct:
		for i := 0; i < val.NumField(); i++ {
			walkValue(val.Field(i))
		}
	case reflect.Slice, reflect.Array:
		for i := 0; i < val.Len(); i++ {
			walkValue(val.Index(i))
		}
	case reflect.Map:
		for _, key := range val.MapKeys() {
			walkValue(val.MapIndex(key))
		}
	case reflect.Chan:
		for {
			if v, ok := val.Recv(); ok {
				walkValue(v)
			} else {
				break
			}
		}
	}
}
```
النوع التالي الذي نريد معالجته هو `func`.

## اكتب الاختبار أولاً

```go
t.Run("with function", func(t *testing.T) {
	aFunction := func() (Profile, Profile) {
		return Profile{33, "Berlin"}, Profile{34, "Katowice"}
	}

	var got []string
	want := []string{"Berlin", "Katowice"}

	walk(aFunction, func(input string) {
		got = append(got, input)
	})

	if !reflect.DeepEqual(got, want) {
		t.Errorf("got %v, want %v", got, want)
	}
})
```

## حاول تشغيل الاختبار

```
--- FAIL: TestWalk (0.00s)
    --- FAIL: TestWalk/with_function (0.00s)
        reflection_test.go:132: got [], want [Berlin Katowice]
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

لا يبدو أن للدوال التي تأخذ وسطاء معنى كبيراً في هذا السيناريو، لكن ينبغي أن نسمح بقيم معادة اعتباطية.

```go
func walk(x interface{}, fn func(input string)) {
	val := getValue(x)

	walkValue := func(value reflect.Value) {
		walk(value.Interface(), fn)
	}

	switch val.Kind() {
	case reflect.String:
		fn(val.String())
	case reflect.Struct:
		for i := 0; i < val.NumField(); i++ {
			walkValue(val.Field(i))
		}
	case reflect.Slice, reflect.Array:
		for i := 0; i < val.Len(); i++ {
			walkValue(val.Index(i))
		}
	case reflect.Map:
		for _, key := range val.MapKeys() {
			walkValue(val.MapIndex(key))
		}
	case reflect.Chan:
		for v, ok := val.Recv(); ok; v, ok = val.Recv() {
			walkValue(v)
		}
	case reflect.Func:
		valFnResult := val.Call(nil)
		for _, res := range valFnResult {
			walkValue(res)
		}
	}
}
```

## الخلاصة

- قدّمنا بعض المفاهيم من الحزمة `reflect`.
- استعملنا العَوْدية للمرور على هياكل بيانات اعتباطية.
- أجرينا إعادة هيكلة تبيّن بأثر رجعي أنها سيئة، لكننا لم ننزعج منها كثيراً. فبالعمل التكراري مع الاختبارات لا يكون الأمر بتلك الخطورة.
- لم نتناول هنا إلا جانباً صغيراً من الانعكاس. [وفي مدونة غو مقال ممتاز يتناول مزيداً من التفاصيل](https://blog.golang.org/laws-of-reflection).
- والآن بعد أن عرفت الانعكاس، ابذل قصارى جهدك لتجنب استعماله.
