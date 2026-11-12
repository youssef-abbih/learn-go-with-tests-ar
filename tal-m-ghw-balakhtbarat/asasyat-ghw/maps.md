# الخرائط

**[تجد كل شيفرة هذا الفصل هنا](https://github.com/quii/learn-go-with-tests/tree/main/maps)**

رأيت في فصل [المصفوفات والشرائح](arrays-and-slices.md) كيف تخزّن القيم بالترتيب. وسننظر الآن في طريقة لتخزين العناصر بمفتاح `key` والبحث عنها بسرعة.

تتيح لك الخرائط (maps) تخزين العناصر بطريقة تشبه القاموس. يمكنك أن تعدّ المفتاح `key` هو الكلمة، والقيمة `value` هي تعريفها. وهل هناك طريقة أفضل لتعلّم الخرائط من بناء قاموسنا الخاص؟

أولاً، بافتراض أن لدينا بالفعل بعض الكلمات مع تعريفاتها في القاموس، فإن بحثنا عن كلمة، فينبغي أن يعيد تعريفها.

## اكتب الاختبار أولاً

في الملف `dictionary_test.go`

```go
package main

import "testing"

func TestSearch(t *testing.T) {
	dictionary := map[string]string{"test": "this is just a test"}

	got := Search(dictionary, "test")
	want := "this is just a test"

	if got != want {
		t.Errorf("got %q want %q given, %q", got, want, "test")
	}
}
```

التصريح عن خريطة يشبه بعض الشيء التصريح عن مصفوفة (array)، إلا أنه يبدأ بالكلمة المحجوزة `map` ويتطلب نوعين. الأول هو نوع المفتاح، ويُكتب داخل `[]`. والثاني هو نوع القيمة، ويأتي مباشرة بعد `[]`.

لنوع المفتاح وضع خاص، فلا يمكن أن يكون إلا نوعاً قابلاً للمقارنة، لأننا دون القدرة على معرفة ما إذا كان مفتاحان متساويين لا نملك وسيلة لضمان أننا نحصل على القيمة الصحيحة. والأنواع القابلة للمقارنة مشروحة بالتفصيل في [مواصفات اللغة](https://golang.org/ref/spec#Comparison_operators).

أما نوع القيمة، فيمكن أن يكون أي نوع (type) تريده، بل يمكن أن يكون خريطة أخرى.

كل ما سوى ذلك في هذا الاختبار (test) ينبغي أن يكون مألوفاً.

## حاول تشغيل الاختبار

بتشغيل `go test` سيفشل المصرِّف (compiler) بالخطأ `./dictionary_test.go:8:9: undefined: Search`.

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من المخرجات

في الملف `dictionary.go`

```go
package main

func Search(dictionary map[string]string, word string) string {
	return ""
}
```

ينبغي أن يفشل اختبارك الآن مع *رسالة خطأ واضحة*

`dictionary_test.go:12: got '' want 'this is just a test' given, 'test'`.

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func Search(dictionary map[string]string, word string) string {
	return dictionary[word]
}
```

استخراج قيمة من خريطة يشبه استخراج قيمة من مصفوفة، بالصياغة `map[key]`.

## أعد الهيكلة

```go
func TestSearch(t *testing.T) {
	dictionary := map[string]string{"test": "this is just a test"}

	got := Search(dictionary, "test")
	want := "this is just a test"

	assertStrings(t, got, want)
}

func assertStrings(t testing.TB, got, want string) {
	t.Helper()

	if got != want {
		t.Errorf("got %q want %q", got, want)
	}
}
```

قررت إنشاء دالة مساعدة باسم `assertStrings` لجعل التنفيذ أعم.

### استعمال نوع مخصص

يمكننا تحسين طريقة استعمال قاموسنا بإنشاء نوع جديد حول الخريطة، وجعل `Search` طريقة (method).

في الملف `dictionary_test.go`:

```go
func TestSearch(t *testing.T) {
	dictionary := Dictionary{"test": "this is just a test"}

	got := dictionary.Search("test")
	want := "this is just a test"

	assertStrings(t, got, want)
}
```

بدأنا باستعمال النوع `Dictionary` الذي لم نعرّفه بعد، ثم استدعينا `Search` على نسخة من `Dictionary`.

ولم نحتج إلى تغيير `assertStrings`.

في الملف `dictionary.go`:

```go
type Dictionary map[string]string

func (d Dictionary) Search(word string) string {
	return d[word]
}
```

أنشأنا هنا النوع `Dictionary` الذي يعمل كغلاف رقيق حول `map`. وبعد تعريف النوع المخصص، يمكننا إنشاء الطريقة `Search`.

## اكتب الاختبار أولاً

كان تنفيذ البحث الأساسي سهلاً جداً، لكن ماذا سيحدث إن قدّمنا كلمة ليست في قاموسنا؟

في الواقع لا نحصل على شيء. وهذا جيد لأن البرنامج يستطيع مواصلة العمل، لكن هناك أسلوباً أفضل، وهو أن تبلّغ الدالة (function) بأن الكلمة ليست في القاموس. وبهذا لا يبقى المستخدم متسائلاً عما إذا كانت الكلمة غير موجودة أم أنها فقط بلا تعريف (قد لا يبدو هذا مفيداً جداً في قاموس، لكنه سيناريو قد يكون محورياً في حالات استعمال أخرى).

```go
func TestSearch(t *testing.T) {
	dictionary := Dictionary{"test": "this is just a test"}

	t.Run("known word", func(t *testing.T) {
		got, _ := dictionary.Search("test")
		want := "this is just a test"

		assertStrings(t, got, want)
	})

	t.Run("unknown word", func(t *testing.T) {
		_, err := dictionary.Search("unknown")
		want := "could not find the word you were looking for"

		if err == nil {
			t.Fatal("expected to get an error.")
		}

		assertStrings(t, err.Error(), want)
	})
}
```

الطريقة المتبعة لمعالجة هذا السيناريو في غو (Go) هي إعادة قيمة ثانية من النوع `Error`.

لاحظ أننا هنا، كما رأينا في [فصل المؤشرات والأخطاء](./pointers-and-errors.md)، نتحقق أولاً من أن الخطأ (error) ليس `nil` كي نؤكد رسالة الخطأ،
ثم نستعمل الطريقة `.Error()` للحصول على السلسلة النصية التي نمررها بعد ذلك إلى التوكيد (assertion).

## حاول تشغيل الاختبار

هذا لا يُصرَّف

```
./dictionary_test.go:18:10: assignment mismatch: 2 variables but 1 values
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من المخرجات

```go
func (d Dictionary) Search(word string) (string, error) {
	return d[word], nil
}
```

ينبغي أن يفشل اختبارك الآن برسالة خطأ أوضح بكثير.

`dictionary_test.go:22: expected to get an error.`

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func (d Dictionary) Search(word string) (string, error) {
	definition, ok := d[word]
	if !ok {
		return "", errors.New("could not find the word you were looking for")
	}

	return definition, nil
}
```

لجعل هذا ينجح، نستعمل خاصية مثيرة للاهتمام في البحث في الخريطة، إذ يمكن أن يعيد قيمتين. والقيمة الثانية منطقية (boolean) تشير إلى ما إذا كان المفتاح قد وُجد بنجاح.

وتتيح لنا هذه الخاصية التمييز بين كلمة غير موجودة وكلمة موجودة لكن بلا تعريف.

## أعد الهيكلة

```go
var ErrNotFound = errors.New("could not find the word you were looking for")

func (d Dictionary) Search(word string) (string, error) {
	definition, ok := d[word]
	if !ok {
		return "", ErrNotFound
	}

	return definition, nil
}
```

يمكننا التخلص من الخطأ السحري في الدالة `Search` باستخراجه إلى متغير (variable). وهذا سيتيح لنا أيضاً اختباراً أفضل.

```go
t.Run("unknown word", func(t *testing.T) {
	_, got := dictionary.Search("unknown")
	if got == nil {
		t.Fatal("expected to get an error.")
	}
	assertError(t, got, ErrNotFound)
})
```
```go
func assertError(t testing.TB, got, want error) {
	t.Helper()

	if !errors.Is(got, want) {
		t.Errorf("got error %q want %q", got, want)
	}
}
```

بإنشاء دالة مساعدة جديدة استطعنا تبسيط اختبارنا، وبدأنا باستعمال المتغير `ErrNotFound` كي لا يفشل اختبارنا إن غيّرنا نص الخطأ في المستقبل.

## اكتب الاختبار أولاً

لدينا طريقة رائعة للبحث في القاموس، لكن لا سبيل لدينا لإضافة كلمات جديدة إليه.

```go
func TestAdd(t *testing.T) {
	dictionary := Dictionary{}
	dictionary.Add("test", "this is just a test")

	want := "this is just a test"
	got, err := dictionary.Search("test")
	if err != nil {
		t.Fatal("should find added word:", err)
	}

	assertStrings(t, got, want)
}
```

نستفيد في هذا الاختبار من الدالة `Search` لنجعل التحقق من القاموس أسهل قليلاً.

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من المخرجات

في الملف `dictionary.go`

```go
func (d Dictionary) Add(word, definition string) {
}
```

ينبغي أن يفشل اختبارك الآن

```
dictionary_test.go:31: should find added word: could not find the word you were looking for
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func (d Dictionary) Add(word, definition string) {
	d[word] = definition
}
```

الإضافة إلى خريطة تشبه أيضاً الإضافة إلى مصفوفة، فكل ما عليك هو تحديد مفتاح وإسناد قيمة إليه.

### المؤشرات والنسخ وما إلى ذلك

من الخصائص المثيرة للاهتمام في الخرائط أنك تستطيع تعديلها دون تمرير عنوانها (مثل `&myMap`)

قد يجعلها هذا _تبدو_ وكأنها "نوع مرجعي"، [لكنها ليست كذلك كما يوضح ديف تشيني](https://dave.cheney.net/2017/04/30/if-a-map-isnt-a-reference-variable-what-is-it).

> قيمة الخريطة مؤشر إلى بنية `runtime.hmap`.

لذا حين تمرر خريطة إلى دالة أو طريقة، فإنك تنسخها فعلاً، لكنك تنسخ جزء المؤشر فقط، لا هيكل البيانات الأساسي الذي يحتوي على البيانات.

ومن المزالق في الخرائط أنها قد تكون قيمة `nil`. فالخريطة `nil` تتصرف كخريطة فارغة عند القراءة، لكن محاولة الكتابة إلى خريطة `nil` ستُطلق ذعراً في وقت التشغيل. يمكنك قراءة المزيد عن الخرائط [هنا](https://blog.golang.org/go-maps-in-action).

لذا لا ينبغي أبداً أن تهيّئ متغير خريطة بقيمة `nil`:

```go
var m map[string]string
```

بل يمكنك تهيئة خريطة فارغة أو استعمال الكلمة المحجوزة `make` لإنشاء خريطة:

```go
var dictionary = map[string]string{}

// OR

var dictionary = make(map[string]string)
```

ينشئ كلا الأسلوبين خريطة تجزئة `hash map` فارغة ويجعلان `dictionary` يشير إليها، وهذا يضمن ألا يحدث ذعر في وقت التشغيل أبداً.

## أعد الهيكلة

ليس في تنفيذنا الكثير مما يمكن إعادة هيكلته، لكن الاختبار يحتاج إلى قليل من التبسيط.

```go
func TestAdd(t *testing.T) {
	dictionary := Dictionary{}
	word := "test"
	definition := "this is just a test"

	dictionary.Add(word, definition)

	assertDefinition(t, dictionary, word, definition)
}

func assertDefinition(t testing.TB, dictionary Dictionary, word, definition string) {
	t.Helper()

	got, err := dictionary.Search(word)
	if err != nil {
		t.Fatal("should find added word:", err)
	}
	assertStrings(t, got, definition)
}
```

أنشأنا متغيرين للكلمة والتعريف، ونقلنا توكيد التعريف إلى دالة مساعدة خاصة به.

تبدو الدالة `Add` جيدة، إلا أننا لم نفكر فيما يحدث حين تكون القيمة التي نحاول إضافتها موجودة أصلاً!

لن تُطلق الخريطة خطأً إن كانت القيمة موجودة، بل ستمضي وتكتب فوق القيمة بالقيمة الجديدة. وقد يكون هذا مريحاً عملياً، لكنه يجعل اسم دالتنا غير دقيق. فلا ينبغي أن تعدّل `Add` القيم الموجودة، بل يجب ألا تضيف إلا كلمات جديدة إلى قاموسنا.

## اكتب الاختبار أولاً

```go
func TestAdd(t *testing.T) {
	t.Run("new word", func(t *testing.T) {
		dictionary := Dictionary{}
		word := "test"
		definition := "this is just a test"

		err := dictionary.Add(word, definition)

		assertError(t, err, nil)
		assertDefinition(t, dictionary, word, definition)
	})

	t.Run("existing word", func(t *testing.T) {
		word := "test"
		definition := "this is just a test"
		dictionary := Dictionary{word: definition}
		err := dictionary.Add(word, "new test")

		assertError(t, err, ErrWordExists)
		assertDefinition(t, dictionary, word, definition)
	})
}
```

عدّلنا في هذا الاختبار `Add` لتعيد خطأً، ونتحقق منه مقابل متغير خطأ جديد هو `ErrWordExists`. وعدّلنا أيضاً الاختبار السابق ليتحقق من أن الخطأ `nil`.

## حاول تشغيل الاختبار

سيفشل المصرِّف لأننا لا نعيد قيمة من `Add`.

```
./dictionary_test.go:30:13: dictionary.Add(word, definition) used as value
./dictionary_test.go:41:13: dictionary.Add(word, "new test") used as value
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من المخرجات

في الملف `dictionary.go`

```go
var (
	ErrNotFound   = errors.New("could not find the word you were looking for")
	ErrWordExists = errors.New("cannot add word because it already exists")
)

func (d Dictionary) Add(word, definition string) error {
	d[word] = definition
	return nil
}
```

نحصل الآن على خطأين آخرين، فنحن ما زلنا نعدّل القيمة، ونعيد خطأً قيمته `nil`.

```
dictionary_test.go:43: got error '%!q(<nil>)' want 'cannot add word because it already exists'
dictionary_test.go:44: got 'new test' want 'this is just a test'
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func (d Dictionary) Add(word, definition string) error {
	_, err := d.Search(word)

	switch err {
	case ErrNotFound:
		d[word] = definition
	case nil:
		return ErrWordExists
	default:
		return err
	}

	return nil
}
```

نستعمل هنا تعليمة `switch` للمطابقة على الخطأ. ووجود `switch` كهذه يوفر شبكة أمان إضافية في حال أعادت `Search` خطأً غير `ErrNotFound`.

## أعد الهيكلة

ليس لدينا الكثير مما يمكن إعادة هيكلته، لكن مع تزايد استعمالنا للأخطاء يمكننا إجراء بعض التعديلات.

```go
const (
	ErrNotFound   = DictionaryErr("could not find the word you were looking for")
	ErrWordExists = DictionaryErr("cannot add word because it already exists")
)

type DictionaryErr string

func (e DictionaryErr) Error() string {
	return string(e)
}
```

جعلنا الأخطاء ثابتة، وتطلّب ذلك أن ننشئ نوعاً خاصاً بنا هو `DictionaryErr` يحقق الواجهة (interface) `error`. يمكنك قراءة المزيد عن التفاصيل في [هذا المقال الممتاز لديف تشيني](https://dave.cheney.net/2016/04/07/constant-errors). وباختصار، يجعل هذا الأخطاء أكثر قابلية لإعادة الاستعمال وغير قابلة للتغيير.

بعد ذلك، لننشئ دالة باسم `Update` لتحديث تعريف كلمة.

## اكتب الاختبار أولاً

```go
func TestUpdate(t *testing.T) {
	word := "test"
	definition := "this is just a test"
	dictionary := Dictionary{word: definition}
	newDefinition := "new definition"

	dictionary.Update(word, newDefinition)

	assertDefinition(t, dictionary, word, newDefinition)
}
```

الدالة `Update` وثيقة الصلة بـ`Add`، وستكون تنفيذنا التالي.

## حاول تشغيل الاختبار

```
./dictionary_test.go:53:2: dictionary.Update undefined (type Dictionary has no field or method Update)
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

نعرف بالفعل كيف نتعامل مع خطأ كهذا، فعلينا تعريف دالتنا.

```go
func (d Dictionary) Update(word, definition string) {}
```

وبعد ذلك، نستطيع أن نرى أن علينا تغيير تعريف الكلمة.

```
dictionary_test.go:55: got 'this is just a test' want 'new definition'
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

رأينا كيف نفعل هذا حين أصلحنا المشكلة في `Add`، فلننفّذ شيئاً مشابهاً جداً لـ`Add`.

```go
func (d Dictionary) Update(word, definition string) {
	d[word] = definition
}
```

لا حاجة إلى أي إعادة هيكلة هنا لأنه كان تغييراً بسيطاً. لكن لدينا الآن المشكلة نفسها التي كانت في `Add`، فإن مررنا كلمة جديدة فستضيفها `Update` إلى القاموس.

## اكتب الاختبار أولاً

```go
t.Run("existing word", func(t *testing.T) {
	word := "test"
	definition := "this is just a test"
	dictionary := Dictionary{word: definition}
	newDefinition := "new definition"

	err := dictionary.Update(word, newDefinition)

	assertError(t, err, nil)
	assertDefinition(t, dictionary, word, newDefinition)
})

t.Run("new word", func(t *testing.T) {
	word := "test"
	definition := "this is just a test"
	dictionary := Dictionary{}

	err := dictionary.Update(word, definition)

	assertError(t, err, ErrWordDoesNotExist)
})
```

أضفنا نوع خطأ آخر لحالة عدم وجود الكلمة، وعدّلنا `Update` لتعيد قيمة `error`.

## حاول تشغيل الاختبار

```
./dictionary_test.go:53:16: dictionary.Update(word, newDefinition) used as value
./dictionary_test.go:64:16: dictionary.Update(word, definition) used as value
./dictionary_test.go:66:23: undefined: ErrWordDoesNotExist
```

نحصل هذه المرة على 3 أخطاء، لكننا نعرف كيف نتعامل معها.

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

```go
const (
	ErrNotFound         = DictionaryErr("could not find the word you were looking for")
	ErrWordExists       = DictionaryErr("cannot add word because it already exists")
	ErrWordDoesNotExist = DictionaryErr("cannot perform operation on word because it does not exist")
)

func (d Dictionary) Update(word, definition string) error {
	d[word] = definition
	return nil
}
```

أضفنا نوع الخطأ الخاص بنا ونعيد خطأً قيمته `nil`.

وبهذه التغييرات نحصل الآن على خطأ واضح جداً:

```
dictionary_test.go:66: got error '%!q(<nil>)' want 'cannot perform operation on word because it does not exist'
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func (d Dictionary) Update(word, definition string) error {
	_, err := d.Search(word)

	switch err {
	case ErrNotFound:
		return ErrWordDoesNotExist
	case nil:
		d[word] = definition
	default:
		return err
	}

	return nil
}
```

تبدو هذه الدالة مطابقة تقريباً لـ`Add`، إلا أننا بدّلنا الحالتين اللتين نحدّث فيهما `dictionary` ونعيد فيهما خطأً.

### ملاحظة عن التصريح عن خطأ جديد للدالة `Update`

كان بإمكاننا إعادة استعمال `ErrNotFound` وعدم إضافة خطأ جديد، لكن من الأفضل غالباً أن يكون هناك خطأ دقيق لحالة فشل التحديث.

فالأخطاء المحددة تعطيك معلومات أكثر عما حدث من خطأ. وإليك مثالاً في تطبيق ويب:

> يمكنك إعادة توجيه المستخدم حين تواجه `ErrNotFound`، لكن تعرض رسالة خطأ حين تواجه `ErrWordDoesNotExist`.

بعد ذلك، لننشئ دالة باسم `Delete` لحذف كلمة من القاموس.

## اكتب الاختبار أولاً

```go
func TestDelete(t *testing.T) {
	word := "test"
	dictionary := Dictionary{word: "test definition"}

	dictionary.Delete(word)

	_, err := dictionary.Search(word)
	assertError(t, err, ErrNotFound)
}
```

ينشئ اختبارنا `Dictionary` فيه كلمة، ثم يتحقق مما إذا كانت الكلمة قد حُذفت.

## حاول تشغيل الاختبار

بتشغيل `go test` نحصل على:

```
./dictionary_test.go:74:6: dictionary.Delete undefined (type Dictionary has no field or method Delete)
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

```go
func (d Dictionary) Delete(word string) {

}
```

بعد أن نضيف هذا، يخبرنا الاختبار بأننا لا نحذف الكلمة.

```
dictionary_test.go:78: got error '%!q(<nil>)' want 'could not find the word you were looking for'
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func (d Dictionary) Delete(word string) {
	delete(d, word)
}
```

لدى غو دالة مدمجة اسمها `delete` تعمل على الخرائط. تأخذ وسيطين (arguments) ولا تعيد شيئاً. الوسيط الأول هو الخريطة، والثاني هو المفتاح المراد حذفه.

## أعد الهيكلة
ليس هناك الكثير مما يمكن إعادة هيكلته، لكن يمكننا تطبيق المنطق نفسه الذي في `Update` لمعالجة الحالات التي لا تكون فيها الكلمة موجودة.

```go
func TestDelete(t *testing.T) {
	t.Run("existing word", func(t *testing.T) {
		word := "test"
		dictionary := Dictionary{word: "test definition"}

		err := dictionary.Delete(word)

		assertError(t, err, nil)

		_, err = dictionary.Search(word)

		assertError(t, err, ErrNotFound)
	})

	t.Run("non-existing word", func(t *testing.T) {
		word := "test"
		dictionary := Dictionary{}

		err := dictionary.Delete(word)

		assertError(t, err, ErrWordDoesNotExist)
	})
}
```

## حاول تشغيل الاختبار

سيفشل المصرِّف لأننا لا نعيد قيمة من `Delete`.

```
./dictionary_test.go:77:10: dictionary.Delete(word) (no value) used as value
./dictionary_test.go:90:10: dictionary.Delete(word) (no value) used as value
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func (d Dictionary) Delete(word string) error {
	_, err := d.Search(word)

	switch err {
	case ErrNotFound:
		return ErrWordDoesNotExist
	case nil:
		delete(d, word)
	default:
		return err
	}

	return nil
}
```

نستعمل مرة أخرى تعليمة `switch` للمطابقة على الخطأ حين نحاول حذف كلمة غير موجودة.

## الخلاصة

تناولنا في هذا القسم الكثير. فقد أنشأنا واجهة برمجية كاملة من نوع CRUD (الإنشاء والقراءة والتحديث والحذف) لقاموسنا. وتعلّمنا خلال ذلك كيف:

* ننشئ الخرائط
* نبحث عن العناصر في الخرائط
* نضيف عناصر جديدة إلى الخرائط
* نحدّث العناصر في الخرائط
* نحذف العناصر من الخريطة
* تعلّمنا المزيد عن الأخطاء
  * كيف ننشئ أخطاء ثابتة
  * كتابة أغلفة للأخطاء
