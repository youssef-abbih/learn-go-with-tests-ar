# قوالب HTML

**[تجد كل الشيفرة هنا](https://github.com/quii/learn-go-with-tests/tree/main/blogrenderer)**

نعيش في عالم يريد فيه الجميع بناء تطبيقات ويب بأحدث إطار عمل للواجهة الأمامية رائج هذا الشهر، مبني على غيغابايتات من JavaScript المحوَّلة، ويعمل مع نظام بناء بيزنطي التعقيد؛ [لكن ربما لا يكون ذلك ضرورياً دائماً](https://quii.dev/The_Web_I_Want).

أستطيع القول إن معظم مطوري غو (Go) يقدّرون سلسلة أدوات بسيطة ومستقرة وسريعة، لكن عالم الواجهة الأمامية كثيراً ما يخفق في تحقيق ذلك.

كثير من المواقع لا تحتاج إلى أن تكون [تطبيق صفحة واحدة (SPA)](https://en.wikipedia.org/wiki/Single-page_application). **فلغتا HTML وCSS وسيلتان رائعتان لتقديم المحتوى**، ويمكنك استعمال غو لصنع موقع يقدّم صفحات HTML للمستخدمين.

وإن أردت مع ذلك بعض العناصر الديناميكية، فما زال بإمكانك نثر قليل من JavaScript على جانب العميل، أو قد ترغب حتى في تجربة [Hotwire](https://hotwired.dev) التي تتيح لك تقديم تجربة ديناميكية بأسلوب يعتمد على جانب الخادم.

يمكنك توليد HTML في غو باستعمال مُتقَن لـ[`fmt.Fprintf`](https://pkg.go.dev/fmt#Fprintf)، لكنك ستتعلم في هذا الفصل أن في مكتبة غو القياسية أدوات لتوليد HTML بطريقة أبسط وأسهل في الصيانة. وستتعلم أيضاً طرقاً أكثر فعالية لاختبار هذا النوع من الشيفرة (code) ربما لم تصادفها من قبل.

## ما سنبنيه

في فصل [قراءة الملفات](/reading-files.md) كتبنا شيفرة تأخذ [`fs.FS`](https://pkg.go.dev/io/fs)  (نظام ملفات)، وتعيد شريحة (slice) من `Post` لكل ملف markdown تصادفه.

```go
posts, err := blogposts.NewPostsFromFS(os.DirFS("posts"))
```

إليك كيف عرّفنا `Post`

```go
type Post struct {
	Title, Description, Body string
	Tags                     []string
}
```

وإليك مثالاً على أحد ملفات markdown التي يمكن تحليلها.

```markdown
Title: Welcome to my blog
Description: Introduction to my blog
Tags: cooking, family, live-laugh-love
---
# First recipe!
Welcome to my **amazing recipe blog**. I am going to write about my family recipes, and make sure I write a long, irrelevant and boring story about my family before you get to the actual instructions.
```

إن واصلنا رحلتنا في كتابة برنامج المدونة، فسنأخذ هذه البيانات ونولّد منها HTML يعيده خادم الويب رداً على طلبات HTTP الواردة.

نريد لمدونتنا توليد نوعين من الصفحات:

1. **عرض التدوينة**. تعرض تدوينة محددة. والحقل `Body` في `Post` سلسلة نصية تحتوي على markdown، لذا ينبغي تحويلها إلى HTML.
2. **الفهرس**. يسرد كل التدوينات، مع روابط لعرض كل تدوينة.

وسنريد أيضاً مظهراً وإحساساً متسقين في موقعنا، لذا سيكون لكل صفحة أثاث HTML المعتاد مثل `<html>` و`<head>` الذي يحتوي على روابط أوراق أنماط CSS وأي شيء آخر قد نريده.

حين تبني برنامج مدونة، تكون أمامك بعض الخيارات في طريقة بناء HTML وإرساله إلى متصفح المستخدم.

سنصمم شيفرتنا بحيث تقبل `io.Writer`. وهذا يعني أن من يستدعي شيفرتنا يملك المرونة في أن:

- يكتب الصفحات إلى [os.File](https://pkg.go.dev/os#File)، كي تُقدَّم بشكل ساكن
- يكتب HTML مباشرة إلى [`http.ResponseWriter`](https://pkg.go.dev/net/http#ResponseWriter)
- أو يكتبها إلى أي شيء في الحقيقة! فما دام يحقق `io.Writer` يستطيع المستخدم توليد HTML من `Post`

## اكتب الاختبار أولاً

كالعادة، من المهم التفكير في المتطلبات قبل الغوص بسرعة. كيف نأخذ هذه المجموعة الكبيرة نسبياً من المتطلبات ونقسمها إلى خطوة صغيرة قابلة للتحقيق نركز عليها؟

في رأيي، عرض المحتوى فعلياً أولى من صفحة الفهرس. فيمكننا إطلاق هذا المنتج ومشاركة روابط مباشرة إلى محتوانا الرائع. أما صفحة فهرس لا تستطيع الربط بالمحتوى الفعلي فليست مفيدة.

ومع ذلك، ما زال عرض تدوينة كما وُصف سابقاً يبدو كبيراً. كل أثاث HTML، وتحويل متن markdown إلى HTML، وسرد الوسوم، وغير ذلك.

في هذه المرحلة لا أهتم كثيراً بالترميز المحدد، وخطوة أولى سهلة هي مجرد التحقق من أننا نستطيع عرض عنوان التدوينة كعنصر `<h1>`. هذه *تبدو* أصغر خطوة أولى يمكن أن تدفعنا إلى الأمام قليلاً.

```go
package blogrenderer_test

import (
	"bytes"
	"github.com/quii/learn-go-with-tests/blogrenderer"
	"testing"
)

func TestRender(t *testing.T) {
	var (
		aPost = blogrenderer.Post{
			Title:       "hello world",
			Body:        "This is a post",
			Description: "This is a description",
			Tags:        []string{"go", "tdd"},
		}
	)

	t.Run("it converts a single post into HTML", func(t *testing.T) {
		buf := bytes.Buffer{}
		err := blogrenderer.Render(&buf, aPost)

		if err != nil {
			t.Fatal(err)
		}

		got := buf.String()
		want := `<h1>hello world</h1>`
		if got != want {
			t.Errorf("got '%s' want '%s'", got, want)
		}
	})
}
```

قرارنا قبول `io.Writer` يجعل الاختبار أيضاً بسيطاً، ففي هذه الحالة نكتب إلى [`bytes.Buffer`](https://pkg.go.dev/bytes#Buffer) الذي يمكننا فحص محتوياته لاحقاً.

## حاول تشغيل الاختبار

إن كنت قد قرأت الفصول السابقة من هذا الكتاب، فينبغي أن تكون متمرّساً في هذا الآن. لن تستطيع تشغيل الاختبار (test) لأن الحزمة (package) والدالة (function) `Render` غير معرّفتين. حاول اتباع رسائل المصرِّف بنفسك والوصول إلى حالة تستطيع فيها تشغيل الاختبار ورؤيته يفشل برسالة واضحة.

من المهم حقاً أن تختبر فشل اختباراتك، فستشكر نفسك حين تُفشل اختباراً عن غير قصد بعد 6 أشهر لأنك بذلت الجهد *الآن* للتحقق من أنه يفشل برسالة واضحة.

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

هذه أقل شيفرة لجعل الاختبار يعمل

```go
package blogrenderer

// if you're continuing from the read files chapter, you shouldn't redefine this
type Post struct {
	Title, Description, Body string
	Tags                     []string
}

func Render(w io.Writer, p Post) error {
	return nil
}
```

ينبغي أن يعترض الاختبار على أن السلسلة النصية الفارغة لا تساوي ما نريد.

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func Render(w io.Writer, p Post) error {
	_, err := fmt.Fprintf(w, "<h1>%s</h1>", p.Title)
	return err
}
```

تذكّر أن تطوير البرمجيات نشاط تعلّم في المقام الأول. ولكي نكتشف ونتعلم ونحن نعمل، علينا أن نعمل بطريقة تمنحنا حلقات تغذية راجعة (feedback loops) متكررة وعالية الجودة، وأسهل طريقة لذلك هي العمل بخطوات صغيرة.

لذا لا نقلق الآن بشأن استعمال أي مكتبات قوالب. فيمكنك صنع HTML بقوالب السلاسل النصية "العادية" دون مشكلة، وبتجاوز جزء القوالب نستطيع التحقق من قدر صغير من السلوك المفيد، وقد أنجزنا جزءاً صغيراً من العمل التصميمي على الواجهة البرمجية لحزمتنا.

## أعد الهيكلة

لا يوجد الكثير مما يمكن إعادة هيكلته بعد، فلننتقل إلى التكرار التالي

## اكتب الاختبار أولاً

والآن بعد أن صارت لدينا نسخة بسيطة جداً تعمل، يمكننا التقدم في الاختبار لتوسيع الوظائف. وفي هذه الحالة، عرض مزيد من المعلومات من `Post`.

```go
	t.Run("it converts a single post into HTML", func(t *testing.T) {
		buf := bytes.Buffer{}
		err := blogrenderer.Render(&buf, aPost)

		if err != nil {
			t.Fatal(err)
		}

		got := buf.String()
		want := `<h1>hello world</h1>
<p>This is a description</p>
Tags: <ul><li>go</li><li>tdd</li></ul>`

		if got != want {
			t.Errorf("got '%s' want '%s'", got, want)
		}
	})
```

لاحظ أن كتابة هذا *تبدو* محرجة. فرؤية كل ذلك الترميز في الاختبار شعور سيئ، ونحن لم نضع حتى المتن، ولا HTML الفعلي الذي نريده مع كل محتوى `<head>` وأي أثاث نحتاج إليه في الصفحة.

ومع ذلك، لنتحمل الألم *في الوقت الحالي*.

## حاول تشغيل الاختبار

ينبغي أن يفشل، معترضاً على أنه لا يحتوي على السلسلة النصية التي نتوقعها، لأننا لا نعرض الوصف والوسوم.

## اكتب ما يكفي من الشيفرة لينجح الاختبار

حاول فعل هذا بنفسك بدلاً من نسخ الشيفرة. ما ستجده أن جعل هذا الاختبار ينجح _مزعج بعض الشيء_! فحين حاولت، ظهر لي هذا الخطأ (error) في محاولتي الأولى

```
=== RUN   TestRender
=== RUN   TestRender/it_converts_a_single_post_into_HTML
    renderer_test.go:32: got '<h1>hello world</h1><p>This is a description</p><ul><li>go</li><li>tdd</li></ul>' want '<h1>hello world</h1>
        <p>This is a description</p>
        Tags: <ul><li>go</li><li></li></ul>'
```

أسطر جديدة! من يهتم؟ حسناً، اختبارنا يهتم، لأنه يطابق على قيمة نصية دقيقة. هل ينبغي له ذلك؟ حذفت الأسطر الجديدة في الوقت الحالي فقط لجعل الاختبار ينجح.

```go
func Render(w io.Writer, p Post) error {
	_, err := fmt.Fprintf(w, "<h1>%s</h1><p>%s</p>", p.Title, p.Description)
	if err != nil {
		return err
	}

	_, err = fmt.Fprint(w, "Tags: <ul>")
	if err != nil {
		return err
	}

	for _, tag := range p.Tags {
		_, err = fmt.Fprintf(w, "<li>%s</li>", tag)
		if err != nil {
			return err
		}
	}

	_, err = fmt.Fprint(w, "</ul>")
	if err != nil {
		return err
	}

	return nil
}
```

**يا للهول**. ليست أجمل شيفرة كتبتها، وما زلنا في تنفيذ مبكر جداً للترميز. سنحتاج إلى محتوى وأشياء أكثر بكثير في صفحتنا، ونرى بسرعة أن هذا الأسلوب غير مناسب.

لكن الأهم أن لدينا اختباراً ناجحاً؛ لدينا برنامج يعمل.

## أعد الهيكلة

مع شبكة الأمان التي يوفرها اختبار ناجح لشيفرة تعمل، يمكننا الآن التفكير في تغيير أسلوب التنفيذ في مرحلة إعادة الهيكلة (refactoring).

### تقديم القوالب

لدى غو حزمتا قوالب، [text/template](https://pkg.go.dev/text/template) و[html/template](https://pkg.go.dev/html/template)، وتشتركان في الواجهة (interface) نفسها.  وكلتاهما تتيح لك دمج قالب مع بعض البيانات لإنتاج سلسلة نصية.

فما الفرق في النسخة الخاصة بـHTML إذن؟

> تنفّذ الحزمة `template` (أي `html/template`) قوالب مقادة بالبيانات لتوليد مخرجات HTML آمنة من حقن الشيفرة. وتوفر الواجهة نفسها التي توفرها الحزمة `text/template`، وينبغي استعمالها بدلاً من `text/template` كلما كانت المخرجات بصيغة HTML تحديداً.

لغة القوالب تشبه كثيراً [Mustache](https://mustache.github.io)، وتتيح لك توليد المحتوى ديناميكياً بطريقة نظيفة جداً مع فصل جميل للاهتمامات. ومقارنة بلغات القوالب الأخرى التي ربما استعملتها، فهي مقيدة جداً، أو "خالية من المنطق" كما تحب Mustache أن تقول. وهذا قرار تصميمي مهم **ومقصود**.

ومع أننا نركز هنا على توليد HTML، فإن كان مشروعك يجري عمليات دمج معقدة للسلاسل النصية وتعاويذ غامضة، فقد ترغب في اللجوء إلى `text/template` لتنظيف شيفرتك.

### العودة إلى الشيفرة

إليك قالباً لمدونتنا:

`<h1>{{.Title}}</h1><p>{{.Description}}</p>Tags: <ul>{{range .Tags}}<li>{{.}}</li>{{end}}</ul>`

أين نعرّف هذه السلسلة النصية؟ حسناً، لدينا بعض الخيارات، لكن لإبقاء الخطوات صغيرة، لنبدأ بسلسلة نصية عادية

```go
package blogrenderer

import (
	"html/template"
	"io"
)

const (
	postTemplate = `<h1>{{.Title}}</h1><p>{{.Description}}</p>Tags: <ul>{{range .Tags}}<li>{{.}}</li>{{end}}</ul>`
)

func Render(w io.Writer, p Post) error {
	templ, err := template.New("blog").Parse(postTemplate)
	if err != nil {
		return err
	}

	if err := templ.Execute(w, p); err != nil {
		return err
	}

	return nil
}
```

ننشئ قالباً جديداً باسم، ثم نحلل سلسلة القالب. ويمكننا بعد ذلك استعمال الطريقة (method) `Execute` عليه، ممررين بياناتنا، وهي في هذه الحالة `Post`.

سيستبدل القالب أشياء مثل `{{.Description}}` بمحتوى `p.Description`. وتوفر القوالب أيضاً بعض الأدوات البرمجية الأساسية مثل `range` للمرور على القيم، و`if`. ويمكنك إيجاد مزيد من التفاصيل في [توثيق text/template](https://pkg.go.dev/text/template).

*ينبغي أن تكون هذه إعادة هيكلة خالصة.* فلا ينبغي أن نحتاج إلى تغيير اختباراتنا، وينبغي أن تظل ناجحة. والمهم أن شيفرتنا أسهل قراءة، وفيها معالجة أخطاء مزعجة أقل بكثير.

كثيراً ما يشكو الناس من إسهاب معالجة الأخطاء في غو، لكنك قد تجد طرقاً أفضل لكتابة شيفرتك بحيث تكون أقل عرضة للأخطاء أصلاً، كما هنا.

### مزيد من إعادة الهيكلة

استعمال `html/template` كان تحسيناً بالتأكيد، لكن وجوده كثابت نصي في شيفرتنا ليس رائعاً:

- ما زال صعب القراءة إلى حد ما.
- ليس ملائماً لبيئة التطوير أو المحرر، فلا تلوين للصياغة، ولا إمكانية لإعادة التنسيق أو إعادة الهيكلة، وغير ذلك.
- يبدو مثل HTML، لكنك لا تستطيع العمل معه كما تعمل مع ملف HTML "عادي"

ما نود فعله هو أن تعيش قوالبنا في ملفات منفصلة كي ننظمها بشكل أفضل، ونعمل معها كأنها ملفات HTML عادية.

أنشئ مجلداً باسم "templates"، وأنشئ داخله ملفاً باسم `blog.gohtml`، والصق قالبنا في الملف.

غيّر الآن شيفرتنا لتضمين أنظمة الملفات باستعمال [ميزة التضمين التي جاءت في غو 1.16](https://pkg.go.dev/embed).

```go
package blogrenderer

import (
	"embed"
	"html/template"
	"io"
)

var (
	//go:embed "templates/*"
	postTemplates embed.FS
)

func Render(w io.Writer, p Post) error {
	templ, err := template.ParseFS(postTemplates, "templates/*.gohtml")
	if err != nil {
		return err
	}

	if err := templ.Execute(w, p); err != nil {
		return err
	}

	return nil
}
```

بتضمين "نظام ملفات" في شيفرتنا، نستطيع تحميل عدة قوالب ودمجها بحرية. وسيصبح هذا مفيداً حين نريد مشاركة منطق العرض بين قوالب مختلفة، مثل ترويسة لأعلى صفحة HTML وتذييل.

### التضمين؟

تطرقنا إلى التضمين بشكل خفيف في فصل [قراءة الملفات](reading-files.md). ويشرح [توثيق المكتبة القياسية](https://pkg.go.dev/embed) ذلك

> توفر الحزمة `embed` الوصول إلى الملفات المضمَّنة في برنامج غو قيد التشغيل.
>
> يمكن لملفات غو المصدرية التي تستورد "embed" استعمال الموجّه `//go:embed` لتهيئة متغير من النوع `string` أو `[]byte` أو `FS` بمحتويات ملفات تُقرأ من مجلد الحزمة أو مجلداتها الفرعية في وقت التصريف.

لماذا نريد استعمال هذا؟ البديل هو أننا _نستطيع_ تحميل قوالبنا من نظام ملفات "عادي". لكن هذا يعني أن علينا التأكد من وجود القوالب في مسار الملف الصحيح أينما أردنا استعمال هذا البرنامج. وقد تكون لديك في عملك بيئات مختلفة مثل التطوير والتجهيز والإنتاج. ولكي يعمل هذا، عليك التأكد من نسخ قوالبك إلى المكان الصحيح.

أما مع التضمين، فتُدرج الملفات في برنامج غو حين تبنيه. وهذا يعني أنك بمجرد أن تبني برنامجك (وهو ما ينبغي أن تفعله مرة واحدة فقط)، تكون الملفات متاحة لك دائماً.

والجميل أنك لا تستطيع تضمين ملفات منفردة فحسب، بل أنظمة ملفات أيضاً؛ ونظام الملفات ذاك يحقق [io/fs](https://pkg.go.dev/io/fs)، مما يعني أن شيفرتك لا تحتاج إلى الاهتمام بنوع نظام الملفات الذي تعمل معه.

لكن إن أردت استعمال قوالب مختلفة بحسب الإعدادات، فقد ترغب في الالتزام بتحميل القوالب من القرص بالطريقة التقليدية.

## التالي: اجعل القالب "جميلاً"

لا نريد حقاً أن يُعرَّف قالبنا كسلسلة نصية في سطر واحد. نريد أن نستطيع توزيعه على أسطر ليسهل قراءته والعمل معه، شيء كهذا:

```handlebars
<h1>{{.Title}}</h1>

<p>{{.Description}}</p>

Tags: <ul>{{range .Tags}}<li>{{.}}</li>{{end}}</ul>
```

لكن إن فعلنا هذا، فسيفشل اختبارنا. وذلك لأن اختبارنا يتوقع إعادة سلسلة نصية محددة جداً.

لكن في الحقيقة، لا تهمنا المسافات البيضاء. وستصبح صيانة هذا الاختبار كابوساً إن اضطررنا إلى تحديث سلسلة التوكيد بعناء في كل مرة نجري فيها تغييرات طفيفة على الترميز. ومع نمو القالب، يصعب التحكم بهذا النوع من التعديلات، وتخرج تكاليف العمل عن السيطرة.

## تقديم اختبارات الموافقة

[اختبارات الموافقة في غو](https://github.com/approvals/go-approval-tests)

> تتيح `ApprovalTests` اختبار الكائنات الكبيرة والسلاسل النصية وأي شيء آخر يمكن حفظه في ملف (الصور والأصوات وملفات CSV وغيرها...) بسهولة

الفكرة تشبه الملفات "الذهبية" أو اختبار اللقطات. فبدلاً من صيانة السلاسل النصية بعناء داخل ملف اختبار، تستطيع أداة الموافقة مقارنة المخرجات لك بملف "معتمد" أنشأته. ثم تنسخ ببساطة النسخة الجديدة إن وافقت عليها. أعد تشغيل الاختبار فتعود إلى الأخضر.

أضف تبعية على `"github.com/approvals/go-approval-tests"` إلى مشروعك، وعدّل الاختبار إلى ما يلي

```go
func TestRender(t *testing.T) {
	var (
		aPost = blogrenderer.Post{
			Title:       "hello world",
			Body:        "This is a post",
			Description: "This is a description",
			Tags:        []string{"go", "tdd"},
		}
	)

	t.Run("it converts a single post into HTML", func(t *testing.T) {
		buf := bytes.Buffer{}

		if err := blogrenderer.Render(&buf, aPost); err != nil {
			t.Fatal(err)
		}

		approvals.VerifyString(t, buf.String())
	})
}
```

في المرة الأولى التي تشغّله فيها سيفشل، لأننا لم نوافق على أي شيء بعد

```
=== RUN   TestRender
=== RUN   TestRender/it_converts_a_single_post_into_HTML
    renderer_test.go:29: Failed Approval: received does not match approved.
```

سيكون قد أنشأ ملفين يبدوان كما يلي

- `renderer_test.TestRender.it_converts_a_single_post_into_HTML.received.txt`
- `renderer_test.TestRender.it_converts_a_single_post_into_HTML.approved.txt`

يحتوي الملف المستلم على النسخة الجديدة غير المعتمدة من المخرجات. انسخها إلى الملف المعتمد الفارغ وأعد تشغيل الاختبار.

بنسخك النسخة الجديدة تكون قد "وافقت" على التغيير، وينجح الاختبار الآن.

لترى سير العمل عملياً، عدّل القالب كما ناقشنا ليصبح أسهل قراءة (لكنه من حيث المعنى هو نفسه).

```handlebars
<h1>{{.Title}}</h1>

<p>{{.Description}}</p>

Tags: <ul>{{range .Tags}}<li>{{.}}</li>{{end}}</ul>
```

أعد تشغيل الاختبار. سيُولَّد ملف "مستلم" جديد لأن مخرجات شيفرتنا تختلف عن النسخة المعتمدة. ألقِ نظرة عليهما، وإن رضيت بالتغييرات فانسخ النسخة الجديدة ببساطة وأعد تشغيل الاختبار. وتأكد من إيداع الملفات المعتمدة في نظام التحكم بالمصدر.

يجعل هذا الأسلوب إدارة التغييرات على الأشياء الكبيرة القبيحة مثل HTML أبسط بكثير. فيمكنك استعمال أداة مقارنة لعرض الفروق وإدارتها، ويُبقي شيفرة اختبارك أنظف.

![استعمل أداة مقارنة لإدارة التغييرات](https://i.imgur.com/0MoNdva.png)

هذا في الحقيقة استعمال بسيط إلى حد ما لاختبارات الموافقة (approval tests)، وهي أداة مفيدة للغاية في ترسانة الاختبار لديك. ولـ[إميلي باش](https://twitter.com/emilybache) [فيديو مثير للاهتمام تستعمل فيه اختبارات الموافقة لإضافة مجموعة واسعة جداً من الاختبارات إلى قاعدة شيفرة معقدة ليس فيها أي اختبار](https://www.youtube.com/watch?v=zyM2Ep28ED8). و"الاختبار التوافقي" شيء يستحق البحث فيه بالتأكيد.

والآن بعد أن أجرينا هذا التغيير، ما زلنا نستفيد من كون شيفرتنا مختبَرة جيداً، لكن الاختبارات لن تعترض طريقنا كثيراً حين نعبث بالترميز.

### هل ما زلنا نمارس `TDD`؟

من الآثار الجانبية المثيرة للاهتمام لهذا الأسلوب أنه يبعدنا عن `TDD`. فبالطبع _يمكنك_ تعديل الملفات المعتمدة يدوياً إلى الحالة التي تريدها، وتشغيل اختباراتك، ثم إصلاح القوالب لتُخرج ما عرّفته.

لكن هذا سخيف! فـ`TDD` أسلوب لأداء العمل، وتحديداً للتصميم؛ لكن هذا لا يعني أن علينا استعماله بتعصب في **كل شيء**.

المهم أننا فعلنا الصواب واستعملنا `TDD` كـ**أداة تصميم** لتصميم الواجهة البرمجية لحزمتنا. أما لتغييرات القوالب فيمكن أن تكون عمليتنا:

- أجرِ تغييراً صغيراً على القالب
- شغّل اختبار الموافقة
- افحص المخرجات بعينك للتأكد من أنها تبدو صحيحة
- اعتمدها
- كرر

وما زال لا ينبغي أن نتخلى عن قيمة العمل بخطوات صغيرة قابلة للتحقيق. حاول إيجاد طرق لجعل التغييرات صغيرة، وواصل إعادة تشغيل الاختبارات للحصول على تغذية راجعة حقيقية عما تفعله.

وإن بدأنا بفعل أشياء مثل تغيير الشيفرة _المحيطة_ بالقوالب، فقد يستدعي ذلك بالطبع العودة إلى أسلوب `TDD` في العمل.

## توسيع الترميز

لمعظم المواقع HTML أغنى مما لدينا الآن. فبدايةً، هناك عنصر `html`، ومعه `head`، وربما `nav` أيضاً. وعادةً هناك فكرة التذييل أيضاً.

إن كان موقعنا سيضم صفحات مختلفة، فسنريد تعريف هذه الأشياء في مكان واحد ليبقى مظهر موقعنا متسقاً. وتدعم قوالب غو تعريف أقسام يمكننا بعد ذلك استيرادها في قوالب أخرى.

عدّل قالبنا الحالي ليستورد قالباً علوياً وقالباً سفلياً

```handlebars
{{template "top" .}}
<h1>{{.Title}}</h1>

<p>{{.Description}}</p>

Tags: <ul>{{range .Tags}}<li>{{.}}</li>{{end}}</ul>
{{template "bottom" .}}
```

ثم أنشئ `top.gohtml` بما يلي

```handlebars
{{define "top"}}
<!DOCTYPE html>
<html lang="en">
<head>
    <title>My amazing blog!</title>
    <meta charset="UTF-8"/>
    <meta name="description" content="Wow, like and subscribe, it really helps the channel guys" lang="en"/>
</head>
<body>
<nav role="navigation">
    <div>
        <h1>Budding Gopher's blog</h1>
        <ul>
            <li><a href="/">home</a></li>
            <li><a href="about">about</a></li>
            <li><a href="archive">archive</a></li>
        </ul>
    </div>
</nav>
<main>
{{end}}
```

و`bottom.gohtml`

```handlebars
{{define "bottom"}}
</main>
<footer>
    <ul>
        <li><a href="https://twitter.com/quii">Twitter</a></li>
        <li><a href="https://github.com/quii">GitHub</a></li>
    </ul>
</footer>
</body>
</html>
{{end}}
```

(بالطبع، لك أن تضع أي ترميز تحبه!)

علينا الآن تحديد قالب معيّن لتشغيله. في عارض المدونة، غيّر الأمر `Execute` إلى `ExecuteTemplate`

```go
if err := templ.ExecuteTemplate(w, "blog.gohtml", p); err != nil {
	return err
}
```

أعد تشغيل اختبارك. ينبغي أن يُنشأ ملف "مستلم" جديد وسيفشل الاختبار. راجعه، وإن رضيت به فاعتمده بنسخه فوق النسخة القديمة. أعد تشغيل الاختبار مرة أخرى وينبغي أن ينجح.

## ذريعة للعبث بقياس الأداء

قبل أن نمضي قدماً، لنفكر فيما تفعله شيفرتنا.

```go
func Render(w io.Writer, p Post) error {
	templ, err := template.ParseFS(postTemplates, "templates/*.gohtml")
	if err != nil {
		return err
	}

	if err := templ.ExecuteTemplate(w, "blog.gohtml", p); err != nil {
		return err
	}

	return nil
}
```

- تحلل القوالب
- تستعمل القالب لعرض تدوينة إلى `io.Writer`

مع أن أثر إعادة تحليل القوالب لكل تدوينة على الأداء سيكون ضئيلاً في معظم الحالات، فإن الجهد اللازم لـ*عدم* فعل ذلك ضئيل أيضاً، وينبغي أن يرتب الشيفرة قليلاً.

لرؤية أثر عدم تكرار هذا التحليل مرة بعد مرة، يمكننا استعمال أداة قياس الأداء (benchmark) لنرى مدى سرعة دالتنا.

```go
func BenchmarkRender(b *testing.B) {
	var (
		aPost = blogrenderer.Post{
			Title:       "hello world",
			Body:        "This is a post",
			Description: "This is a description",
			Tags:        []string{"go", "tdd"},
		}
	)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		blogrenderer.Render(io.Discard, aPost)
	}
}
```

إليك النتائج على حاسوبي

```
BenchmarkRender-8 22124 53812 ns/op
```

لكي لا نضطر إلى إعادة تحليل القوالب مرة بعد مرة، سننشئ نوعاً (type) يحتفظ بالقالب المحلَّل، وتكون له طريقة تتولى العرض

```go
type PostRenderer struct {
	templ *template.Template
}

func NewPostRenderer() (*PostRenderer, error) {
	templ, err := template.ParseFS(postTemplates, "templates/*.gohtml")
	if err != nil {
		return nil, err
	}

	return &PostRenderer{templ: templ}, nil
}

func (r *PostRenderer) Render(w io.Writer, p Post) error {

	if err := r.templ.ExecuteTemplate(w, "blog.gohtml", p); err != nil {
		return err
	}

	return nil
}
```

هذا يغيّر واجهة شيفرتنا، لذا سنحتاج إلى تحديث اختبارنا

```go
func TestRender(t *testing.T) {
	var (
		aPost = blogrenderer.Post{
			Title:       "hello world",
			Body:        "This is a post",
			Description: "This is a description",
			Tags:        []string{"go", "tdd"},
		}
	)

	postRenderer, err := blogrenderer.NewPostRenderer()

	if err != nil {
		t.Fatal(err)
	}

	t.Run("it converts a single post into HTML", func(t *testing.T) {
		buf := bytes.Buffer{}

		if err := postRenderer.Render(&buf, aPost); err != nil {
			t.Fatal(err)
		}

		approvals.VerifyString(t, buf.String())
	})
}
```

وقياس أدائنا

```go
func BenchmarkRender(b *testing.B) {
	var (
		aPost = blogrenderer.Post{
			Title:       "hello world",
			Body:        "This is a post",
			Description: "This is a description",
			Tags:        []string{"go", "tdd"},
		}
	)

	postRenderer, err := blogrenderer.NewPostRenderer()

	if err != nil {
		b.Fatal(err)
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		postRenderer.Render(io.Discard, aPost)
	}
}
```

ينبغي أن يظل الاختبار ناجحاً. فماذا عن قياس الأداء؟

النتيجة الآن `BenchmarkRender-8 362124 3131 ns/op`. وكانت النانوثواني لكل عملية سابقاً `53812 ns/op`، لذا فهذا تحسين جيد! ومع إضافة طرق أخرى للعرض، كصفحة فهرس مثلاً، ينبغي أن تصبح الشيفرة أبسط لأننا لا نحتاج إلى تكرار تحليل القوالب.

## العودة إلى العمل الحقيقي

فيما يخص عرض التدوينات، الجزء المهم المتبقي هو عرض `Body` فعلياً. فإن كنت تذكر، ينبغي أن يكون markdown كتبه المؤلف، لذا سيحتاج إلى تحويله إلى صيغة HTML قبل عرضه.

سنترك هذا تمريناً لك أيها القارئ. ينبغي أن تستطيع إيجاد مكتبة غو تفعل هذا لك. واستعمل اختبار الموافقة للتحقق مما تفعله.

### عن اختبار مكتبات الأطراف الثالثة

**ملاحظة**. احرص على ألا تنشغل كثيراً باختبار سلوك مكتبة طرف ثالث صراحةً في اختبارات الوحدة.

كتابة اختبارات على شيفرة لا تتحكم بها هدر للجهد، وتضيف أعباء صيانة. وقد ترغب أحياناً في استعمال [حقن التبعية](./dependency-injection.md) للتحكم بتبعية ما ومحاكاة سلوكها في اختبار.

لكنني في هذه الحالة أرى تحويل markdown إلى HTML تفصيلاً من تفاصيل تنفيذ العرض، وينبغي أن تمنحنا اختبارات الموافقة ثقة كافية.

### عرض الفهرس

الجزء التالي من الوظائف الذي سننفذه هو عرض الفهرس، أي سرد التدوينات كقائمة HTML مرقمة.

نحن نوسّع واجهتنا البرمجية، لذا سنعيد ارتداء قبعة `TDD`.

## اكتب الاختبار أولاً

تبدو صفحة الفهرس بسيطة للوهلة الأولى، لكن كتابة الاختبار ما زالت تدفعنا إلى اتخاذ بعض القرارات التصميمية

```go
t.Run("it renders an index of posts", func(t *testing.T) {
	buf := bytes.Buffer{}
	posts := []blogrenderer.Post{{Title: "Hello World"}, {Title: "Hello World 2"}}

	if err := postRenderer.RenderIndex(&buf, posts); err != nil {
		t.Fatal(err)
	}

	got := buf.String()
	want := `<ol><li><a href="/post/hello-world">Hello World</a></li><li><a href="/post/hello-world-2">Hello World 2</a></li></ol>`

	if got != want {
		t.Errorf("got %q want %q", got, want)
	}
})
```

1. نستعمل حقل العنوان في `Post` كجزء من مسار عنوان URL، لكننا لا نريد مسافات في العنوان، لذا نستبدلها بشرطات.
2. أضفنا الطريقة `RenderIndex` إلى `PostRenderer`، وهي تأخذ مرة أخرى `io.Writer` وشريحة من `Post`.

لو التزمنا هنا بأسلوب الاختبار بعد الشيفرة مع اختبارات الموافقة، لما أجبنا عن هذه الأسئلة في بيئة متحكم بها. **الاختبارات تمنحنا مساحة للتفكير**.

## حاول تشغيل الاختبار

```
./renderer_test.go:41:13: undefined: blogrenderer.RenderIndex
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

```go
func (r *PostRenderer) RenderIndex(w io.Writer, posts []Post) error {
	return nil
}
```

ينبغي أن يؤدي ما سبق إلى فشل الاختبار التالي

```
=== RUN   TestRender
=== RUN   TestRender/it_renders_an_index_of_posts
    renderer_test.go:49: got "" want "<ol><li><a href=\"/post/hello-world\">Hello World</a></li><li><a href=\"/post/hello-world-2\">Hello World 2</a></li></ol>"
--- FAIL: TestRender (0.00s)
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

مع أن هذا _يبدو_ سهلاً، فهو محرج بعض الشيء. فعلته على عدة خطوات

```go
func (r *PostRenderer) RenderIndex(w io.Writer, posts []Post) error {
	indexTemplate := `<ol>{{range .}}<li><a href="/post/{{.Title}}">{{.Title}}</a></li>{{end}}</ol>`

	templ, err := template.New("index").Parse(indexTemplate)
	if err != nil {
		return err
	}

	if err := templ.Execute(w, posts); err != nil {
		return err
	}

	return nil
}
```

لم أرد الانشغال بملفات قوالب منفصلة في البداية، بل أردت فقط أن يعمل. وأرى أن التحليل المسبق للقوالب وفصلها إعادة هيكلة يمكنني فعلها لاحقاً.

هذا لا ينجح، لكنه قريب.

```
=== RUN   TestRender
=== RUN   TestRender/it_renders_an_index_of_posts
    renderer_test.go:49: got "<ol><li><a href=\"/post/Hello%20World\">Hello World</a></li><li><a href=\"/post/Hello%20World%202\">Hello World 2</a></li></ol>" want "<ol><li><a href=\"/post/hello-world\">Hello World</a></li><li><a href=\"/post/hello-world-2\">Hello World 2</a></li></ol>"
--- FAIL: TestRender (0.00s)
    --- FAIL: TestRender/it_renders_an_index_of_posts (0.00s)
```

يمكنك أن ترى أن شيفرة القوالب تهرّب المسافات في سمات `href`. ونحتاج إلى طريقة لاستبدال المسافات بشرطات في السلسلة النصية. ولا نستطيع ببساطة المرور على `[]Post` واستبدالها في الذاكرة، لأننا ما زلنا نريد عرض المسافات للمستخدم في نصوص الروابط.

لدينا بعض الخيارات. أولها سنستكشفه هو تمرير دالة إلى قالبنا.

### تمرير الدوال إلى القوالب

```go
func (r *PostRenderer) RenderIndex(w io.Writer, posts []Post) error {
	indexTemplate := `<ol>{{range .}}<li><a href="/post/{{sanitiseTitle .Title}}">{{.Title}}</a></li>{{end}}</ol>`

	templ, err := template.New("index").Funcs(template.FuncMap{
		"sanitiseTitle": func(title string) string {
			return strings.ToLower(strings.Replace(title, " ", "-", -1))
		},
	}).Parse(indexTemplate)
	if err != nil {
		return err
	}

	if err := templ.Execute(w, posts); err != nil {
		return err
	}

	return nil
}
```

_قبل أن تحلل قالباً_ يمكنك إضافة `template.FuncMap` إلى قالبك، وهي تتيح لك تعريف دوال يمكن استدعاؤها داخل القالب. وفي هذه الحالة أنشأنا الدالة `sanitiseTitle` التي نستدعيها بعد ذلك داخل قالبنا بكتابة `{{sanitiseTitle .Title}}`.

هذه ميزة قوية، فالقدرة على إرسال الدوال إلى قالبك ستتيح لك فعل أشياء رائعة جداً، لكن هل ينبغي لك ذلك؟ بالعودة إلى مبادئ Mustache والقوالب الخالية من المنطق، لماذا دعت إلى الخلو من المنطق؟ **ما الخطأ في وجود المنطق في القوالب؟**

كما بيّنّا، لكي نختبر قوالبنا *اضطررنا إلى تقديم نوع مختلف تماماً من الاختبار*.

تخيّل أنك أدخلت إلى قالب دالة لسلوكها عدة تبديلات وحالات حدّية، **فكيف ستختبرها**؟ مع هذا التصميم الحالي، وسيلتك الوحيدة لاختبار هذا المنطق هي _عرض HTML ومقارنة السلاسل النصية_. وهذه ليست طريقة سهلة ولا عاقلة لاختبار المنطق، وبالتأكيد ليست ما تريده لمنطق الأعمال _المهم_.

ومع أن أسلوب اختبارات الموافقة خفّض تكلفة صيانة هذه الاختبارات، فما زالت صيانتها أغلى من معظم اختبارات الوحدة التي ستكتبها. وما زالت حساسة لأي تغيير طفيف في الترميز، كل ما في الأمر أننا جعلنا إدارتها أسهل. وينبغي مع ذلك أن نسعى إلى هندسة شيفرتنا بحيث لا نحتاج إلى كتابة اختبارات كثيرة حول قوالبنا، وأن نحاول فصل الاهتمامات بحيث يُفصل كما ينبغي أي منطق لا حاجة إلى أن يعيش داخل شيفرة العرض.

ما تمنحك إياه محركات القوالب المتأثرة بـMustache قيد مفيد، فلا تحاول الالتفاف عليه كثيراً؛ **لا تسبح عكس التيار**. بل تبنَّ فكرة [نماذج العرض](https://stackoverflow.com/a/11074506/3193)، حيث تبني أنواعاً مخصصة تحتوي على البيانات التي تحتاج إلى عرضها، بطريقة مريحة للغة القوالب.

وبهذه الطريقة، أياً كان منطق الأعمال المهم الذي تستعمله لتوليد تلك الحزمة من البيانات، يمكن اختباره باختبارات الوحدة منفصلاً، بعيداً عن عالم HTML والقوالب الفوضوي.

### فصل الاهتمامات

فماذا يمكننا أن نفعل بدلاً من ذلك؟

#### أضف طريقة إلى `Post` ثم استدعها في القالب

يمكننا في شيفرة القوالب استدعاء طرق على الأنواع التي نرسلها، لذا يمكننا إضافة الطريقة `SanitisedTitle` إلى `Post`. وهذا سيبسّط القالب، ويمكننا بسهولة اختبار هذا المنطق باختبارات الوحدة منفصلاً إن أردنا. وهذا على الأرجح الحل الأسهل، وإن لم يكن بالضرورة الأبسط.

ومن عيوب هذا الأسلوب أن هذا ما زال منطق _عرض_. فهو لا يهم بقية النظام، لكنه يصبح الآن جزءاً من الواجهة البرمجية لكائن أساسي في المجال. وهذا النوع من الأساليب قد يقودك مع الوقت إلى إنشاء [كائنات إلهية](https://en.wikipedia.org/wiki/God_object).

#### أنشئ نوع نموذج عرض مخصصاً، مثل `PostViewModel`، يحتوي على البيانات التي نحتاج إليها بالضبط

فبدلاً من أن تقترن شيفرة العرض بكائن المجال `Post`، تأخذ نموذج عرض.

```go
type PostViewModel struct {
	Title, SanitisedTitle, Description, Body string
	Tags                                     []string
}
```

سيضطر مستدعو شيفرتنا إلى التحويل من `[]Post` إلى `[]PostView`، مع توليد `SanitizedTitle`. ومن طرق إبقاء ذلك نظيفاً وجود دالة `func NewPostView(p Post) PostView` تغلّف هذا التحويل.

سيُبقي هذا شيفرة العرض خالية من المنطق، وهو على الأرجح أشد فصل للاهتمامات يمكننا فعله، لكن المقابل هو عملية أعقد قليلاً لعرض تدويناتنا.

كلا الخيارين جيد، وأنا في هذه الحالة أميل إلى الأول. ومع تطوير النظام، ينبغي أن تحذر من إضافة مزيد من الطرق المرتجلة لمجرد تسهيل العرض؛ فنماذج العرض المخصصة تصبح أكثر فائدة حين يصبح التحويل بين كائن المجال والعرض أكثر تعقيداً.

لذا يمكننا إضافة طريقتنا إلى `Post`

```go
func (p Post) SanitisedTitle() string {
	return strings.ToLower(strings.Replace(p.Title, " ", "-", -1))
}
```

ثم يمكننا العودة إلى عالم أبسط في شيفرة العرض

```go
func (r *PostRenderer) RenderIndex(w io.Writer, posts []Post) error {
	indexTemplate := `<ol>{{range .}}<li><a href="/post/{{.SanitisedTitle}}">{{.Title}}</a></li>{{end}}</ol>`

	templ, err := template.New("index").Parse(indexTemplate)
	if err != nil {
		return err
	}

	if err := templ.Execute(w, posts); err != nil {
		return err
	}

	return nil
}
```

## أعد الهيكلة

أخيراً ينبغي أن ينجح الاختبار. ويمكننا الآن نقل قالبنا إلى ملف (`templates/index.gohtml`) وتحميله مرة واحدة، حين نبني العارض.

```go
package blogrenderer

import (
	"embed"
	"html/template"
	"io"
)

var (
	//go:embed "templates/*"
	postTemplates embed.FS
)

type PostRenderer struct {
	templ *template.Template
}

func NewPostRenderer() (*PostRenderer, error) {
	templ, err := template.ParseFS(postTemplates, "templates/*.gohtml")
	if err != nil {
		return nil, err
	}

	return &PostRenderer{templ: templ}, nil
}

func (r *PostRenderer) Render(w io.Writer, p Post) error {
	return r.templ.ExecuteTemplate(w, "blog.gohtml", p)
}

func (r *PostRenderer) RenderIndex(w io.Writer, posts []Post) error {
	return r.templ.ExecuteTemplate(w, "index.gohtml", posts)
}
```

بتحليل أكثر من قالب في `templ`، صار علينا الآن استدعاء `ExecuteTemplate` وتحديد _أي_ قالب نريد عرضه بحسب الحاجة، لكن أرجو أن توافقني على أن الشيفرة التي وصلنا إليها تبدو رائعة.

هناك خطر _طفيف_ في أنه إن غيّر أحدهم اسم أحد ملفات القوالب فسيُدخل خطأً برمجياً، لكن اختبارات الوحدة السريعة لدينا ستكتشف ذلك بسرعة.

والآن بعد أن رضينا بتصميم الواجهة البرمجية لحزمتنا، وصرنا نملك بعض السلوك الأساسي المبني بـ`TDD`، لنغيّر اختبارنا ليستعمل اختبارات الموافقة.

```go
	t.Run("it renders an index of posts", func(t *testing.T) {
		buf := bytes.Buffer{}
		posts := []blogrenderer.Post{{Title: "Hello World"}, {Title: "Hello World 2"}}

		if err := postRenderer.RenderIndex(&buf, posts); err != nil {
			t.Fatal(err)
		}

		approvals.VerifyString(t, buf.String())
	})
```

تذكّر أن تشغّل الاختبار لتراه يفشل، ثم اعتمد التغيير.

وأخيراً يمكننا إضافة أثاث الصفحة إلى صفحة الفهرس:

```handlebars
{{template "top" .}}
<ol>{{range .}}<li><a href="/post/{{.SanitisedTitle}}">{{.Title}}</a></li>{{end}}</ol>
{{template "bottom" .}}
```

أعد تشغيل الاختبار، واعتمد التغيير، وننتهي من الفهرس!

## عرض متن markdown

شجعتك على أن تجربه بنفسك، وإليك الأسلوب الذي انتهيت إليه.

```go
package blogrenderer

import (
	"embed"
	"github.com/gomarkdown/markdown"
	"github.com/gomarkdown/markdown/parser"
	"html/template"
	"io"
)

var (
	//go:embed "templates/*"
	postTemplates embed.FS
)

type PostRenderer struct {
	templ    *template.Template
	mdParser *parser.Parser
}

func NewPostRenderer() (*PostRenderer, error) {
	templ, err := template.ParseFS(postTemplates, "templates/*.gohtml")
	if err != nil {
		return nil, err
	}

	extensions := parser.CommonExtensions | parser.AutoHeadingIDs
	parser := parser.NewWithExtensions(extensions)

	return &PostRenderer{templ: templ, mdParser: parser}, nil
}

func (r *PostRenderer) Render(w io.Writer, p Post) error {
	return r.templ.ExecuteTemplate(w, "blog.gohtml", newPostVM(p, r))
}

func (r *PostRenderer) RenderIndex(w io.Writer, posts []Post) error {
	return r.templ.ExecuteTemplate(w, "index.gohtml", posts)
}

type postViewModel struct {
	Post
	HTMLBody template.HTML
}

func newPostVM(p Post, r *PostRenderer) postViewModel {
	vm := postViewModel{Post: p}
	vm.HTMLBody = template.HTML(markdown.ToHTML([]byte(p.Body), r.mdParser, nil))
	return vm
}
```

استعملت مكتبة [gomarkdown](https://github.com/gomarkdown/markdown) الممتازة التي عملت تماماً كما كنت آمل.

إن حاولت فعل هذا بنفسك، فربما وجدت أن عرض المتن عندك قد هرّب HTML. وهذه ميزة أمنية في الحزمة `html/template` في غو لمنع إخراج HTML خبيث من طرف ثالث.

وللالتفاف على ذلك، عليك في النوع الذي ترسله إلى العرض أن تغلّف HTML الموثوق به في [template.HTML](https://pkg.go.dev/html/template#HTML)

> يغلّف النوع `HTML` جزءاً من مستند HTML معروفاً بأنه آمن. ولا ينبغي استعماله مع HTML قادم من طرف ثالث، أو HTML فيه وسوم أو تعليقات غير مغلقة. أما مخرجات أداة تعقيم HTML سليمة، وقالب هرّبته هذه الحزمة، فلا بأس باستعمالها مع `HTML`.
>
> استعمال هذا النوع يمثّل خطراً أمنياً: يجب أن يأتي المحتوى المغلَّف من مصدر موثوق، لأنه سيُدرج حرفياً في مخرجات القالب.

لذا أنشأت نموذج عرض **غير مُصدَّر** (`postViewModel`)، لأنني ما زلت أراه تفصيلاً داخلياً من تفاصيل تنفيذ العرض. فلا حاجة لي إلى اختباره منفصلاً، ولا أريده أن يلوّث واجهتي البرمجية.

أبني واحداً عند العرض كي أستطيع تحليل `Body` إلى `HTMLBody`، ثم أستعمل ذلك الحقل في القالب لعرض HTML الناتج.

## الخلاصة

إن جمعت ما تعلّمته في فصل [قراءة الملفات](reading-files.md) وهذا الفصل، فستستطيع بسهولة صنع مولّد مواقع ساكنة بسيط ومختبَر جيداً، وإطلاق مدونة خاصة بك. ابحث عن بعض دروس CSS وستستطيع جعلها تبدو جميلة أيضاً.

يتجاوز هذا الأسلوب المدونات. فأخذ البيانات من أي مصدر، سواء كان قاعدة بيانات أو واجهة برمجية أو نظام ملفات، وتحويلها إلى HTML وإعادتها من خادم، أسلوب بسيط يمتد عبر عقود كثيرة. ويحب الناس التذمر من تعقيد تطوير الويب الحديث، لكن هل أنت متأكد من أنك لا تفرض التعقيد على نفسك؟

غو رائعة لتطوير الويب، خصوصاً حين تفكر بوضوح في متطلباتك الحقيقية للموقع الذي تصنعه. ومقارنة بإنشاء "تطبيق ويب" بتقنيات مثل React، كثيراً ما يكون توليد HTML على الخادم أسلوباً أفضل وأبسط وأعلى أداءً.

### ما تعلمناه

- كيف تنشئ قوالب HTML وتعرضها.
- كيف تركّب القوالب معاً، وتزيل التكرار ([DRY](https://en.wikipedia.org/wiki/Don't_repeat_yourself)) من الترميز المترابط، وتحافظ على مظهر متسق.
- كيف تمرر الدوال إلى القوالب، ولماذا ينبغي أن تفكر مرتين قبل ذلك.
- كيف تكتب "اختبارات الموافقة"، التي تساعدنا على اختبار المخرجات الكبيرة القبيحة لأشياء مثل عارضات القوالب.

### عن القوالب الخالية من المنطق

كالعادة، الأمر كله يدور حول **فصل الاهتمامات**. فمن المهم أن ننظر في مسؤوليات الأجزاء المختلفة من نظامنا. وكثيراً ما يسرّب الناس منطق الأعمال المهم إلى القوالب، فيخلطون الاهتمامات ويجعلون الأنظمة صعبة الفهم والصيانة والاختبار.

### ليست لـHTML فقط

تذكّر أن لدى غو `text/template` لتوليد أنواع أخرى من البيانات من قالب. فإن وجدت نفسك تحتاج إلى تحويل البيانات إلى نوع من المخرجات المنظمة، فقد تفيدك الأساليب المعروضة في هذا الفصل.

### مراجع ومواد إضافية

- يضم موقع [John Calhoun's 'Learn Web Development with Go'](https://www.calhoun.io/intro-to-templates-p1-contextual-encoding/) عدداً من المقالات الممتازة عن القوالب.
- مكتبة [Hotwire](https://hotwired.dev): يمكنك استعمال هذه الأساليب لإنشاء تطبيقات ويب بـHotwire. وقد بنتها Basecamp، وهي شركة تعمل أساساً بـRuby on Rails، لكن لأنها تعمل على جانب الخادم، يمكننا استعمالها مع غو.
