# قراءة الملفات

- **[تجد كل شيفرة هذا الفصل هنا](https://github.com/quii/learn-go-with-tests/tree/main/reading-files)**
- [إليك فيديو أعمل فيه على المشكلة وأجيب عن أسئلة البث المباشر على Twitch](https://www.youtube.com/watch?v=nXts4dEJnkU)

سنتعلم في هذا الفصل كيف نقرأ بعض الملفات، ونستخرج منها بعض البيانات، ونفعل شيئاً مفيداً.

تخيّل أنك تعمل مع صديقك على إنشاء برنامج للمدونات. والفكرة أن يكتب المؤلف تدويناته بصيغة markdown، مع بعض البيانات الوصفية في أعلى الملف. وعند بدء التشغيل، سيقرأ خادم الويب مجلداً لإنشاء بعض قيم `Post`، ثم تستعمل دالة (function) منفصلة هي `NewHandler` قيم `Post` هذه مصدراً للبيانات لخادم الويب الخاص بالمدونة.

طُلب منا إنشاء الحزمة (package) التي تحوّل مجلداً معيّناً من ملفات التدوينات إلى مجموعة من قيم `Post`.

### بيانات المثال

الملف `hello world.md`

```markdown
Title: Hello, TDD world!
Description: First post on our wonderful blog
Tags: tdd, go
---
Hello world!

The body of posts starts after the `---`
```

### البيانات المتوقعة

```go
type Post struct {
	Title, Description, Body string
	Tags                     []string
}
```

## التطوير التكراري المقاد بالاختبارات

سنتبع أسلوباً تكرارياً نتخذ فيه دائماً خطوات بسيطة وآمنة نحو هدفنا.

وهذا يتطلب منا تقسيم عملنا، لكن ينبغي أن نحذر من الوقوع في فخ اتباع أسلوب ["من الأسفل إلى الأعلى"](https://en.wikipedia.org/wiki/Top-down_and_bottom-up_design).

لا ينبغي أن نثق بخيالنا المفرط في النشاط حين نبدأ العمل. فقد نُغرى بصنع نوع من التجريد لا يُتحقق منه إلا حين نجمع كل شيء معاً، مثل `BlogPostFileParser` ما.

هذا _ليس_ تكرارياً، ويفوّت حلقات التغذية الراجعة (feedback loops) المتقاربة التي يُفترض أن يمنحنا إياها `TDD`.

يقول كينت بيك:

> التفاؤل خطر مهني في البرمجة، والتغذية الراجعة هي العلاج.

بل ينبغي أن يسعى أسلوبنا إلى الاقتراب بأسرع ما يمكن من تقديم قيمة _حقيقية_ للمستهلك (وكثيراً ما يسمى هذا "المسار الناجح"). وبمجرد أن نقدّم قدراً صغيراً من القيمة للمستهلك من البداية إلى النهاية، يصبح التقدم في بقية المتطلبات عادةً أمراً مباشراً.

## التفكير في نوع الاختبار الذي نريد رؤيته

لنذكّر أنفسنا بطريقة تفكيرنا وأهدافنا حين نبدأ:

- **اكتب الاختبار الذي تريد رؤيته**. فكّر في كيف نحب أن نستعمل الشيفرة (code) التي سنكتبها من وجهة نظر المستهلك.
- ركّز على _ماذا_ و_لماذا_، ولا تنشغل بـ_كيف_.

تحتاج حزمتنا إلى تقديم دالة يمكن توجيهها إلى مجلد، فتعيد لنا بعض التدوينات.

```go
var posts []blogposts.Post
posts = blogposts.NewPostsFromFS("some-folder")
```

لكتابة اختبار (test) حول هذا، سنحتاج إلى مجلد اختبار ما فيه بعض التدوينات النموذجية. _ليس في هذا خطأ فادح_، لكنك تقبل ببعض المقايضات:

- قد تحتاج في كل اختبار إلى إنشاء ملفات جديدة لاختبار سلوك معيّن
- سيكون اختبار بعض السلوك صعباً، مثل الفشل في تحميل الملفات
- ستعمل الاختبارات أبطأ قليلاً لأنها ستحتاج إلى الوصول إلى نظام الملفات

كما أننا نربط أنفسنا دون داعٍ بتنفيذ محدد لنظام الملفات.

### تجريدات نظام الملفات التي قدّمتها غو 1.16

قدّمت غو (Go) 1.16 تجريداً لأنظمة الملفات هو الحزمة [io/fs](https://golang.org/pkg/io/fs/).

> تعرّف الحزمة `fs` واجهات أساسية لنظام الملفات. ويمكن أن يوفر نظام الملفات نظامُ التشغيل المضيف، لكن يمكن أن توفره أيضاً حزم أخرى.

وهذا يتيح لنا تخفيف اقتراننا بنظام ملفات محدد، مما يتيح لنا بعد ذلك حقن تنفيذات مختلفة بحسب احتياجاتنا.

> [على جانب منتِج الواجهة، يحقق النوع الجديد `embed.FS` الواجهة `fs.FS`، وكذلك يفعل `zip.Reader`. وتوفر الدالة الجديدة `os.DirFS` تنفيذاً لـ`fs.FS` مدعوماً بشجرة من ملفات نظام التشغيل.](https://golang.org/doc/go1.16#fs)

إن استعملنا هذه الواجهة (interface)، فستكون لدى مستخدمي حزمتنا خيارات عديدة جاهزة في المكتبة القياسية. وتعلّم الاستفادة من الواجهات المعرّفة في مكتبة غو القياسية (مثل `io.fs` و[`io.Reader`](https://golang.org/pkg/io/#Reader) و[`io.Writer`](https://golang.org/pkg/io/#Writer)) أمر حيوي لكتابة حزم ضعيفة الاقتران. ويمكن بعد ذلك إعادة استعمال هذه الحزم في سياقات تختلف عما تخيلته، بأقل قدر من العناء على مستهلكيك.

في حالتنا، ربما يريد مستهلكنا تضمين التدوينات في الملف التنفيذي لغو بدلاً من ملفات في نظام ملفات "حقيقي"؟ وفي كلتا الحالتين، _لا تحتاج شيفرتنا إلى الاهتمام_.

ولاختباراتنا، تقدّم لنا الحزمة [testing/fstest](https://golang.org/pkg/testing/fstest/) تنفيذاً لـ[io/FS](https://golang.org/pkg/io/fs/#FS) نستعمله، يشبه الأدوات التي ألفناها في [net/http/httptest](https://golang.org/pkg/net/http/httptest/).

وبناءً على هذه المعلومات، يبدو ما يلي أسلوباً أفضل،

```go
var posts []blogposts.Post
posts = blogposts.NewPostsFromFS(someFS)
```


## اكتب الاختبار أولاً

ينبغي أن نُبقي النطاق صغيراً ومفيداً قدر الإمكان. فإن أثبتنا أننا نستطيع قراءة كل الملفات في مجلد، فستكون تلك بداية جيدة.  وهذا سيمنحنا الثقة في البرنامج الذي نكتبه.  ويمكننا التحقق من أن عدد عناصر `[]Post` المعادة يساوي عدد الملفات في نظام ملفاتنا المزيف.

أنشئ مشروعاً جديداً لتعمل عليه خلال هذا الفصل.

* `mkdir blogposts`
* `cd blogposts`
* `go mod init github.com/{your-name}/blogposts`
* `touch blogposts_test.go`

```go
package blogposts_test

import (
	"testing"
	"testing/fstest"
)

func TestNewBlogPosts(t *testing.T) {
	fs := fstest.MapFS{
		"hello world.md":  {Data: []byte("hi")},
		"hello-world2.md": {Data: []byte("hola")},
	}

	posts := blogposts.NewPostsFromFS(fs)

	if len(posts) != len(fs) {
		t.Errorf("got %d posts, wanted %d posts", len(posts), len(fs))
	}
}
```

لاحظ أن حزمة اختبارنا هي `blogposts_test`. وتذكّر أنه حين يُمارس `TDD` جيداً فإننا نتبع أسلوباً _مقاداً بالمستهلك_: فلا نريد اختبار التفاصيل الداخلية لأن _المستهلكين_ لا يهتمون بها. وبإلحاق `_test` باسم الحزمة المقصودة، لا نصل إلا إلى العناصر المُصدَّرة من حزمتنا، تماماً كما يفعل مستخدم حقيقي لها.

استوردنا [`testing/fstest`](https://golang.org/pkg/testing/fstest/) التي تتيح لنا الوصول إلى النوع [`fstest.MapFS`](https://golang.org/pkg/testing/fstest/#MapFS). وسيمرر نظام ملفاتنا المزيف `fstest.MapFS` إلى حزمتنا.

> النوع `MapFS` نظام ملفات بسيط في الذاكرة للاستعمال في الاختبارات، ممثَّل كخريطة من أسماء المسارات (الوسطاء الممررة إلى `Open`) إلى معلومات عن الملفات أو المجلدات التي تمثلها.

يبدو هذا أبسط من صيانة مجلد من ملفات الاختبار، وسيُنفَّذ أسرع.

وأخيراً، جسّدنا طريقة استعمال واجهتنا البرمجية من وجهة نظر المستهلك، ثم تحققنا من أنها تُنشئ العدد الصحيح من التدوينات.

## حاول تشغيل الاختبار

```
./blogpost_test.go:15:12: undefined: blogposts
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار و_تحقق من مخرجات الاختبار الفاشل_

الحزمة غير موجودة. أنشئ ملفاً جديداً باسم `blogposts.go` وضع فيه `package blogposts`. وستحتاج بعد ذلك إلى استيراد تلك الحزمة في اختباراتك. وعندي صارت الاستيرادات تبدو هكذا:

```go
import (
	blogposts "github.com/quii/learn-go-with-tests/reading-files"
	"testing"
	"testing/fstest"
)
```

لن تُصرَّف الاختبارات الآن لأن حزمتنا الجديدة لا تحتوي على دالة `NewPostsFromFS` تعيد نوعاً ما من المجموعات.

```
./blogpost_test.go:16:12: undefined: blogposts.NewPostsFromFS
```

وهذا يجبرنا على صنع هيكل دالتنا لتشغيل الاختبار. تذكّر ألا تُفرط في التفكير في الشيفرة في هذه المرحلة، فنحن نحاول فقط الحصول على اختبار يعمل، والتأكد من أنه يفشل كما نتوقع. فإن تجاوزنا هذه الخطوة فقد نتجاوز افتراضات، ونكتب اختباراً غير مفيد.

```go
package blogposts

import "testing/fstest"

type Post struct {
}

func NewPostsFromFS(fileSystem fstest.MapFS) []Post {
	return nil
}
```

ينبغي أن يفشل الاختبار الآن بشكل صحيح

```
=== RUN   TestNewBlogPosts
    blogposts_test.go:48: got 0 posts, wanted 2 posts
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

_يمكننا_ أن ["نلفّق"](https://deniseyu.github.io/leveling-up-tdd/) هذا لجعله ينجح:

```go
func NewPostsFromFS(fileSystem fstest.MapFS) []Post {
	return []Post{{}, {}}
}
```

لكن كما كتبت دينيس يو:

>التلفيق مفيد لإعطاء كائنك "هيكلاً عظمياً". فتصميم الواجهة وتنفيذ المنطق اهتمامان منفصلان، والتلفيق الاستراتيجي في الاختبارات يتيح لك التركيز على واحد منهما في كل مرة.

لدينا بالفعل الشكل العام. فماذا نفعل بدلاً من ذلك؟

بما أننا قلّصنا النطاق، فكل ما علينا فعله هو قراءة المجلد وإنشاء تدوينة لكل ملف نصادفه. لا نحتاج إلى القلق بشأن فتح الملفات وتحليلها بعد.

```go
func NewPostsFromFS(fileSystem fstest.MapFS) []Post {
	dir, _ := fs.ReadDir(fileSystem, ".")
	var posts []Post
	for range dir {
		posts = append(posts, Post{})
	}
	return posts
}
```

تقرأ [`fs.ReadDir`](https://golang.org/pkg/io/fs/#ReadDir) مجلداً داخل `fs.FS` معيّن، وتعيد [`[]DirEntry`](https://golang.org/pkg/io/fs/#DirEntry).

لقد أُحبطت نظرتنا المثالية للعالم بالفعل لأن الأخطاء قد تحدث، لكن تذكّر أن تركيزنا الآن على _جعل الاختبار ينجح_، لا على تغيير التصميم، لذا سنتجاهل الخطأ (error) في الوقت الحالي.

بقية الشيفرة مباشرة: نمر على المدخلات، وننشئ `Post` لكل منها، ثم نعيد الشريحة (slice).

## أعد الهيكلة

مع أن اختباراتنا تنجح، لا نستطيع استعمال حزمتنا الجديدة خارج هذا السياق، لأنها مقترنة بتنفيذ ملموس هو `fstest.MapFS`. لكن ليس من الضروري أن تكون كذلك. غيّر وسيط (argument) الدالة `NewPostsFromFS` ليقبل الواجهة الموجودة في المكتبة القياسية.

```go
func NewPostsFromFS(fileSystem fs.FS) []Post {
	dir, _ := fs.ReadDir(fileSystem, ".")
	var posts []Post
	for range dir {
		posts = append(posts, Post{})
	}
	return posts
}
```

أعد تشغيل الاختبارات: ينبغي أن يعمل كل شيء.

### معالجة الأخطاء

أجّلنا معالجة الأخطاء سابقاً حين ركزنا على جعل المسار الناجح يعمل. وقبل مواصلة التقدم في الوظائف، ينبغي أن نقر بأن الأخطاء قد تحدث عند العمل مع الملفات. فإلى جانب قراءة المجلد، قد نواجه مشكلات حين نفتح الملفات منفردة. لنغيّر واجهتنا البرمجية (عبر اختباراتنا أولاً، بطبيعة الحال) كي تستطيع إعادة `error`.

```go
func TestNewBlogPosts(t *testing.T) {
	fs := fstest.MapFS{
		"hello world.md":  {Data: []byte("hi")},
		"hello-world2.md": {Data: []byte("hola")},
	}

	posts, err := blogposts.NewPostsFromFS(fs)

	if err != nil {
		t.Fatal(err)
	}

	if len(posts) != len(fs) {
		t.Errorf("got %d posts, wanted %d posts", len(posts), len(fs))
	}
}
```

شغّل الاختبار: ينبغي أن يعترض على عدد القيم المعادة الخاطئ. وإصلاح الشيفرة أمر مباشر.

```go
func NewPostsFromFS(fileSystem fs.FS) ([]Post, error) {
	dir, err := fs.ReadDir(fileSystem, ".")
	if err != nil {
		return nil, err
	}
	var posts []Post
	for range dir {
		posts = append(posts, Post{})
	}
	return posts, nil
}
```

هذا سيجعل الاختبار ينجح. وقد ينزعج ممارس `TDD` الذي بداخلك لأننا لم نرَ اختباراً فاشلاً قبل كتابة الشيفرة التي تنشر الخطأ القادم من `fs.ReadDir`. ولفعل هذا "كما ينبغي"، سنحتاج إلى اختبار جديد نحقن فيه بديل اختبار (test double) من `fs.FS` يفشل، لجعل `fs.ReadDir` تعيد `error`.

```go
type StubFailingFS struct {
}

func (s StubFailingFS) Open(name string) (fs.File, error) {
	return nil, errors.New("oh no, i always fail")
}
```

```go
// later
_, err := blogposts.NewPostsFromFS(StubFailingFS{})
```

ينبغي أن يمنحك هذا الثقة في أسلوبنا. فالواجهة التي نستعملها لها طريقة (method) واحدة، مما يجعل إنشاء بدائل اختبار لاختبار سيناريوهات مختلفة أمراً بسيطاً.

في بعض الحالات يكون اختبار معالجة الأخطاء هو التصرف العملي، لكننا في حالتنا لا نفعل أي شيء _مثير للاهتمام_ بالخطأ، بل ننشره فقط، لذا لا يستحق الأمر عناء كتابة اختبار جديد.

منطقياً، ستدور تكراراتنا التالية حول توسيع النوع `Post` كي يحتوي على بيانات مفيدة.

## اكتب الاختبار أولاً

سنبدأ بالسطر الأول من مخطط التدوينة المقترح، أي حقل العنوان.

علينا تغيير محتويات ملفات الاختبار لتطابق ما حُدد، ثم يمكننا إجراء توكيد (assertion) على أنه يُحلَّل بشكل صحيح.

```go
func TestNewBlogPosts(t *testing.T) {
	fs := fstest.MapFS{
		"hello world.md":  {Data: []byte("Title: Post 1")},
		"hello-world2.md": {Data: []byte("Title: Post 2")},
	}

	// rest of test code cut for brevity
	got := posts[0]
	want := blogposts.Post{Title: "Post 1"}

	if !reflect.DeepEqual(got, want) {
		t.Errorf("got %+v, want %+v", got, want)
	}
}
```

## حاول تشغيل الاختبار

```
./blogpost_test.go:58:26: unknown field 'Title' in struct literal of type blogposts.Post
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

أضف الحقل الجديد إلى النوع `Post` كي يعمل الاختبار

```go
type Post struct {
	Title string
}
```

أعد تشغيل الاختبار، وينبغي أن تحصل على اختبار فاشل واضح

```
=== RUN   TestNewBlogPosts
=== RUN   TestNewBlogPosts/parses_the_post
    blogpost_test.go:61: got {Title:}, want {Title:Post 1}
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

علينا فتح كل ملف ثم استخراج العنوان

```go
func NewPostsFromFS(fileSystem fs.FS) ([]Post, error) {
	dir, err := fs.ReadDir(fileSystem, ".")
	if err != nil {
		return nil, err
	}
	var posts []Post
	for _, f := range dir {
		post, err := getPost(fileSystem, f)
		if err != nil {
			return nil, err //todo: needs clarification, should we totally fail if one file fails? or just ignore?
		}
		posts = append(posts, post)
	}
	return posts, nil
}

func getPost(fileSystem fs.FS, f fs.DirEntry) (Post, error) {
	postFile, err := fileSystem.Open(f.Name())
	if err != nil {
		return Post{}, err
	}
	defer postFile.Close()

	postData, err := io.ReadAll(postFile)
	if err != nil {
		return Post{}, err
	}

	post := Post{Title: string(postData)[7:]}
	return post, nil
}
```

تذكّر أن تركيزنا في هذه المرحلة ليس كتابة شيفرة أنيقة، بل مجرد الوصول إلى نقطة يكون لدينا فيها برنامج يعمل.

مع أن هذا يبدو تقدماً صغيراً، فقد تطلّب منا كتابة قدر لا بأس به من الشيفرة ووضع بعض الافتراضات بشأن معالجة الأخطاء. وهذه نقطة ينبغي أن تتحدث فيها مع زملائك وتقرروا أفضل أسلوب.

لقد منحنا الأسلوب التكراري تغذية راجعة سريعة بأن فهمنا للمتطلبات غير مكتمل.

تتيح لنا `fs.FS` فتح ملف داخلها باسمه عبر طريقتها `Open`. ومن هناك نقرأ البيانات من الملف، ولا نحتاج الآن إلى أي تحليل متطور، بل نقتطع فقط النص `Title:` بتقطيع السلسلة النصية.

## أعد الهيكلة

فصل "شيفرة فتح الملف" عن "شيفرة تحليل محتويات الملف" سيجعل الشيفرة أبسط في الفهم والعمل.

```go
func getPost(fileSystem fs.FS, f fs.DirEntry) (Post, error) {
	postFile, err := fileSystem.Open(f.Name())
	if err != nil {
		return Post{}, err
	}
	defer postFile.Close()
	return newPost(postFile)
}

func newPost(postFile fs.File) (Post, error) {
	postData, err := io.ReadAll(postFile)
	if err != nil {
		return Post{}, err
	}

	post := Post{Title: string(postData)[7:]}
	return post, nil
}
```

حين تستخرج دوالاً أو طرقاً جديدة بإعادة الهيكلة، فاحرص على التفكير في الوسطاء. فأنت تصمم هنا، وأنت حر في التفكير بعمق فيما هو مناسب لأن لديك اختبارات ناجحة. فكّر في الاقتران والتماسك. وفي هذه الحالة ينبغي أن تسأل نفسك:

> هل يجب أن تقترن `newPost` بـ`fs.File`؟ هل نستعمل كل طرق هذا النوع وبياناته؟ ما الذي نحتاج إليه _حقاً_؟

في حالتنا لا نستعمله إلا كوسيط لـ`io.ReadAll` التي تحتاج إلى `io.Reader`. لذا ينبغي أن نخفف الاقتران في دالتنا ونطلب `io.Reader`.

```go
func newPost(postFile io.Reader) (Post, error) {
	postData, err := io.ReadAll(postFile)
	if err != nil {
		return Post{}, err
	}

	post := Post{Title: string(postData)[7:]}
	return post, nil
}
```

يمكنك تقديم حجة مشابهة للدالة `getPost`، التي تأخذ وسيطاً من النوع `fs.DirEntry` لكنها لا تفعل إلا استدعاء `Name()` للحصول على اسم الملف. لا نحتاج إلى كل ذلك؛ لنفك الاقتران بذلك النوع ونمرر اسم الملف كسلسلة نصية. إليك الشيفرة بعد إعادة هيكلتها بالكامل:

```go
func NewPostsFromFS(fileSystem fs.FS) ([]Post, error) {
	dir, err := fs.ReadDir(fileSystem, ".")
	if err != nil {
		return nil, err
	}
	var posts []Post
	for _, f := range dir {
		post, err := getPost(fileSystem, f.Name())
		if err != nil {
			return nil, err //todo: needs clarification, should we totally fail if one file fails? or just ignore?
		}
		posts = append(posts, post)
	}
	return posts, nil
}

func getPost(fileSystem fs.FS, fileName string) (Post, error) {
	postFile, err := fileSystem.Open(fileName)
	if err != nil {
		return Post{}, err
	}
	defer postFile.Close()
	return newPost(postFile)
}

func newPost(postFile io.Reader) (Post, error) {
	postData, err := io.ReadAll(postFile)
	if err != nil {
		return Post{}, err
	}

	post := Post{Title: string(postData)[7:]}
	return post, nil
}
```

من الآن فصاعداً، يمكن احتواء معظم جهودنا بشكل أنيق داخل `newPost`. فقد انتهينا من مسألتي فتح الملفات والمرور عليها، ويمكننا الآن التركيز على استخراج البيانات للنوع `Post`. ومع أن ذلك ليس ضرورياً تقنياً، فالملفات وسيلة جميلة لتجميع الأشياء المترابطة منطقياً، لذا نقلت النوع `Post` والدالة `newPost` إلى ملف جديد `post.go`.

### دالة مساعدة للاختبار

ينبغي أن نعتني باختباراتنا أيضاً. فسنجري كثيراً من التوكيدات على `Posts`، لذا ينبغي أن نكتب بعض الشيفرة لتساعدنا على ذلك

```go
func assertPost(t *testing.T, got blogposts.Post, want blogposts.Post) {
	t.Helper()
	if !reflect.DeepEqual(got, want) {
		t.Errorf("got %+v, want %+v", got, want)
	}
}
```

```go
assertPost(t, posts[0], blogposts.Post{Title: "Post 1"})
```

## اكتب الاختبار أولاً

لنوسّع اختبارنا أكثر لاستخراج السطر التالي من الملف، أي الوصف. وينبغي أن تكون الخطوات حتى جعله ينجح مريحة ومألوفة الآن.

```go
func TestNewBlogPosts(t *testing.T) {
	const (
		firstBody = `Title: Post 1
Description: Description 1`
		secondBody = `Title: Post 2
Description: Description 2`
	)

	fs := fstest.MapFS{
		"hello world.md":  {Data: []byte(firstBody)},
		"hello-world2.md": {Data: []byte(secondBody)},
	}

	// rest of test code cut for brevity
	assertPost(t, posts[0], blogposts.Post{
		Title:       "Post 1",
		Description: "Description 1",
	})

}
```

## حاول تشغيل الاختبار

```
./blogpost_test.go:47:58: unknown field 'Description' in struct literal of type blogposts.Post
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

أضف الحقل الجديد إلى `Post`.

```go
type Post struct {
	Title       string
	Description string
}
```

ينبغي أن تُصرَّف الاختبارات الآن، وأن تفشل.

```
=== RUN   TestNewBlogPosts
    blogpost_test.go:47: got {Title:Post 1
        Description: Description 1 Description:}, want {Title:Post 1 Description:Description 1}
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

في المكتبة القياسية مكتبة مفيدة تساعدك على المسح عبر البيانات سطراً سطراً: [`bufio.Scanner`](https://golang.org/pkg/bufio/#Scanner)

> يوفر `Scanner` واجهة مريحة لقراءة البيانات، مثل ملف من أسطر نصية مفصولة بمحرف السطر الجديد.

```go
func newPost(postFile io.Reader) (Post, error) {
	scanner := bufio.NewScanner(postFile)

	scanner.Scan()
	titleLine := scanner.Text()

	scanner.Scan()
	descriptionLine := scanner.Text()

	return Post{Title: titleLine[7:], Description: descriptionLine[13:]}, nil
}
```

ومن حسن الحظ أنه يأخذ أيضاً `io.Reader` ليقرأ منه (شكراً مرة أخرى للاقتران الضعيف)، فلا نحتاج إلى تغيير وسطاء دالتنا.

استدعِ `Scan` لقراءة سطر، ثم استخرج البيانات باستعمال `Text`.

هذه الدالة لا يمكن أن تعيد `error` أبداً. وقد يكون من المغري في هذه المرحلة حذفه من نوع القيمة المعادة، لكننا نعرف أننا سنضطر لاحقاً إلى معالجة صيغ الملفات غير الصالحة، فلنتركه.

## أعد الهيكلة

لدينا تكرار في مسح سطر ثم قراءة النص. ونعرف أننا سنفعل هذه العملية مرة أخرى على الأقل، وإزالة هذا التكرار إعادة هيكلة بسيطة، فلنبدأ بها.

```go
func newPost(postFile io.Reader) (Post, error) {
	scanner := bufio.NewScanner(postFile)

	readLine := func() string {
		scanner.Scan()
		return scanner.Text()
	}

	title := readLine()[7:]
	description := readLine()[13:]

	return Post{Title: title, Description: description}, nil
}
```

لم يوفّر هذا تقريباً أي أسطر من الشيفرة، لكن هذا نادراً ما يكون الهدف من إعادة الهيكلة. ما أحاول فعله هنا هو فصل _ماذا_ عن _كيف_ في قراءة الأسطر، لجعل الشيفرة أكثر تصريحية للقارئ قليلاً.

ومع أن العددين السحريين 7 و13 يؤديان المهمة، فإنهما ليسا وصفيين على الإطلاق.

```go
const (
	titleSeparator       = "Title: "
	descriptionSeparator = "Description: "
)

func newPost(postFile io.Reader) (Post, error) {
	scanner := bufio.NewScanner(postFile)

	readLine := func() string {
		scanner.Scan()
		return scanner.Text()
	}

	title := readLine()[len(titleSeparator):]
	description := readLine()[len(descriptionSeparator):]

	return Post{Title: title, Description: description}, nil
}
```

والآن وأنا أحدّق في الشيفرة بعقلي المبدع في إعادة الهيكلة، أود أن أجرّب جعل الدالة `readLine` تتولى إزالة الوسم. وهناك أيضاً طريقة أسهل قراءة لاقتطاع بادئة من سلسلة نصية باستعمال الدالة `strings.TrimPrefix`.

```go
func newPost(postBody io.Reader) (Post, error) {
	scanner := bufio.NewScanner(postBody)

	readMetaLine := func(tagName string) string {
		scanner.Scan()
		return strings.TrimPrefix(scanner.Text(), tagName)
	}

	return Post{
		Title:       readMetaLine(titleSeparator),
		Description: readMetaLine(descriptionSeparator),
	}, nil
}
```

قد تعجبك هذه الفكرة وقد لا تعجبك، لكنها تعجبني. والمقصود أننا في حالة إعادة الهيكلة (refactoring) أحرار في التلاعب بالتفاصيل الداخلية، ويمكنك مواصلة تشغيل اختباراتك للتحقق من أن الأمور ما زالت تتصرف بشكل صحيح. ويمكننا دائماً العودة إلى حالات سابقة إن لم نكن راضين. فأسلوب `TDD` يمنحنا هذا الترخيص لتجربة الأفكار كثيراً، فتكون لدينا فرص أكثر لكتابة شيفرة رائعة.

المتطلب التالي هو استخراج وسوم التدوينة. إن كنت تتابع، فأنصحك بمحاولة تنفيذه بنفسك قبل متابعة القراءة. ينبغي أن يكون لديك الآن إيقاع تكراري جيد، وأن تشعر بالثقة لاستخراج السطر التالي وتحليل بياناته.

اختصاراً، لن أمر بخطوات `TDD`، لكن إليك الاختبار مع إضافة الوسوم.

```go
func TestNewBlogPosts(t *testing.T) {
	const (
		firstBody = `Title: Post 1
Description: Description 1
Tags: tdd, go`
		secondBody = `Title: Post 2
Description: Description 2
Tags: rust, borrow-checker`
	)

	// rest of test code cut for brevity
	assertPost(t, posts[0], blogposts.Post{
		Title:       "Post 1",
		Description: "Description 1",
		Tags:        []string{"tdd", "go"},
	})
}
```

لن تغش إلا نفسك إن نسخت ما أكتبه ولصقته فحسب. وللتأكد من أننا جميعاً على الصفحة نفسها، إليك شيفرتي التي تتضمن استخراج الوسوم.

```go
const (
	titleSeparator       = "Title: "
	descriptionSeparator = "Description: "
	tagsSeparator        = "Tags: "
)

func newPost(postBody io.Reader) (Post, error) {
	scanner := bufio.NewScanner(postBody)

	readMetaLine := func(tagName string) string {
		scanner.Scan()
		return strings.TrimPrefix(scanner.Text(), tagName)
	}

	return Post{
		Title:       readMetaLine(titleSeparator),
		Description: readMetaLine(descriptionSeparator),
		Tags:        strings.Split(readMetaLine(tagsSeparator), ", "),
	}, nil
}
```

أرجو ألا تكون هناك مفاجآت هنا. فقد استطعنا إعادة استعمال `readMetaLine` للحصول على السطر التالي للوسوم، ثم تقسيمها باستعمال `strings.Split`.

التكرار الأخير على مسارنا الناجح هو استخراج متن التدوينة.

إليك تذكيراً بصيغة الملف المقترحة.

```markdown
Title: Hello, TDD world!
Description: First post on our wonderful blog
Tags: tdd, go
---
Hello world!

The body of posts starts after the `---`
```

قرأنا الأسطر الثلاثة الأولى بالفعل. ثم علينا قراءة سطر آخر وتجاهله، وبعد ذلك تحتوي بقية الملف على متن التدوينة.

## اكتب الاختبار أولاً

غيّر بيانات الاختبار لتحتوي على الفاصل، وعلى متن فيه بعض الأسطر الجديدة للتحقق من أننا نلتقط كل المحتوى.

```go
	const (
		firstBody = `Title: Post 1
Description: Description 1
Tags: tdd, go
---
Hello
World`
		secondBody = `Title: Post 2
Description: Description 2
Tags: rust, borrow-checker
---
B
L
M`
	)
```

أضف إلى توكيدنا كما في البقية

```go
	assertPost(t, posts[0], blogposts.Post{
		Title:       "Post 1",
		Description: "Description 1",
		Tags:        []string{"tdd", "go"},
		Body: `Hello
World`,
	})
```

## حاول تشغيل الاختبار

```
./blogpost_test.go:60:3: unknown field 'Body' in struct literal of type blogposts.Post
```

كما كنا نتوقع.

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

أضف `Body` إلى `Post`، وينبغي أن يفشل الاختبار.

```
=== RUN   TestNewBlogPosts
    blogposts_test.go:38: got {Title:Post 1 Description:Description 1 Tags:[tdd go] Body:}, want {Title:Post 1 Description:Description 1 Tags:[tdd go] Body:Hello
        World}
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

1. امسح السطر التالي لتجاهل الفاصل `---`.
2. واصل المسح حتى لا يبقى شيء.

```go
func newPost(postBody io.Reader) (Post, error) {
	scanner := bufio.NewScanner(postBody)

	readMetaLine := func(tagName string) string {
		scanner.Scan()
		return strings.TrimPrefix(scanner.Text(), tagName)
	}

	title := readMetaLine(titleSeparator)
	description := readMetaLine(descriptionSeparator)
	tags := strings.Split(readMetaLine(tagsSeparator), ", ")

	scanner.Scan() // ignore a line

	var b strings.Builder
	for scanner.Scan() {
		fmt.Fprintln(&b, scanner.Text())
	}
	body := strings.TrimSuffix(b.String(), "\n")

	return Post{
		Title:       title,
		Description: description,
		Tags:        tags,
		Body:        body,
	}, nil
}
```

- تعيد `scanner.Scan()` قيمة `bool` تشير إلى ما إذا كانت هناك بيانات أخرى للمسح، لذا يمكننا استعمالها مع حلقة (loop) `for` لمواصلة قراءة البيانات حتى النهاية.
- بعد كل `Scan()` نكتب البيانات في المخزن المؤقت باستعمال `fmt.Fprintln`. ونستعمل النسخة التي تضيف سطراً جديداً لأن الماسح يحذف الأسطر الجديدة من كل سطر، لكننا نحتاج إلى الحفاظ عليها.
- وبسبب ما سبق، علينا اقتطاع السطر الجديد الأخير، كي لا يبقى سطر جديد زائد في النهاية.

## أعد الهيكلة

تغليف فكرة الحصول على بقية البيانات في دالة سيساعد القراء مستقبلاً على أن يفهموا بسرعة _ما_ يحدث في `newPost`، دون الاضطرار إلى الانشغال بتفاصيل التنفيذ.

```go
func newPost(postBody io.Reader) (Post, error) {
	scanner := bufio.NewScanner(postBody)

	readMetaLine := func(tagName string) string {
		scanner.Scan()
		return strings.TrimPrefix(scanner.Text(), tagName)
	}

	return Post{
		Title:       readMetaLine(titleSeparator),
		Description: readMetaLine(descriptionSeparator),
		Tags:        strings.Split(readMetaLine(tagsSeparator), ", "),
		Body:        readBody(scanner),
	}, nil
}

func readBody(scanner *bufio.Scanner) string {
	scanner.Scan() // ignore a line
	var b strings.Builder
	for scanner.Scan() {
		fmt.Fprintln(&b, scanner.Text())
	}
	return strings.TrimSuffix(b.String(), "\n")
}
```

## مزيد من التكرار

صنعنا "الخيط الفولاذي" للوظائف، باتخاذ أقصر طريق للوصول إلى المسار الناجح، لكن من الواضح أن أمامنا مسافة قبل أن يصبح جاهزاً للإنتاج.

لم نعالج بعد:

- حالة أن تكون صيغة الملف غير صحيحة
- حالة ألا يكون الملف من نوع `.md`
- ماذا لو كان ترتيب حقول البيانات الوصفية مختلفاً؟ هل ينبغي السماح بذلك؟ هل ينبغي أن نستطيع معالجته؟

لكن الأهم أن لدينا برنامجاً يعمل، وقد عرّفنا واجهتنا. وما سبق ليس إلا تكرارات أخرى، واختبارات أخرى نكتبها لتقود سلوكنا. ولدعم أي مما سبق لا ينبغي أن نحتاج إلى تغيير _تصميمنا_، بل تفاصيل التنفيذ فقط.

التركيز على الهدف يعني أننا اتخذنا القرارات المهمة، وتحققنا منها مقابل السلوك المطلوب، بدلاً من الغرق في مسائل لن تؤثر في التصميم العام.

## الخلاصة

يقدّم لنا `fs.FS` والتغييرات الأخرى في غو 1.16 طرقاً أنيقة لقراءة البيانات من أنظمة الملفات واختبارها ببساطة.

إن أردت تجربة الشيفرة "على أرض الواقع":

- أنشئ مجلداً باسم `cmd` داخل المشروع، وأضف ملف `main.go`
- أضف الشيفرة التالية

```go
import (
	blogposts "github.com/quii/fstest-spike"
	"log"
	"os"
)

func main() {
	posts, err := blogposts.NewPostsFromFS(os.DirFS("posts"))
	if err != nil {
		log.Fatal(err)
	}
	log.Println(posts)
}
```

- أضف بعض ملفات markdown إلى مجلد `posts` وشغّل البرنامج!

لاحظ التناظر بين شيفرة الإنتاج

```go
posts, err := blogposts.NewPostsFromFS(os.DirFS("posts"))
```

والاختبارات

```go
posts, err := blogposts.NewPostsFromFS(fs)
```

هنا _يبدو_ `TDD` المقاد بالمستهلك ومن الأعلى إلى الأسفل _صحيحاً_.

يستطيع مستخدم حزمتنا النظر إلى اختباراتنا وفهم ما يُفترض أن تفعله وكيفية استعمالها بسرعة. وبصفتنا القائمين على صيانتها، يمكننا أن _نثق بأن اختباراتنا مفيدة لأنها مكتوبة من وجهة نظر المستهلك_. فنحن لا نختبر تفاصيل التنفيذ أو تفاصيل عرضية أخرى، لذا يمكننا أن نثق إلى حد معقول بأن اختباراتنا ستساعدنا، لا أن تعيقنا، عند إعادة الهيكلة.

وبالاعتماد على ممارسات جيدة في هندسة البرمجيات مثل  [**حقن التبعية**](dependency-injection.md) تصبح شيفرتنا سهلة الاختبار وإعادة الاستعمال.

حين تنشئ حزماً، حتى لو كانت داخلية في مشروعك فقط، ففضّل أسلوباً من الأعلى إلى الأسفل مقاداً بالمستهلك. فهذا سيمنعك من الإفراط في تخيّل التصاميم وصنع تجريدات قد لا تحتاج إليها أصلاً، وسيساعد على ضمان أن تكون الاختبارات التي تكتبها مفيدة.

أبقى الأسلوب التكراري كل خطوة صغيرة، وساعدتنا التغذية الراجعة المستمرة على كشف المتطلبات غير الواضحة ربما أبكر مما لو اتبعنا أساليب أخرى أكثر ارتجالاً.

### الكتابة؟

من المهم أن تلاحظ أن هذه الميزات الجديدة لا تحتوي إلا على عمليات _قراءة_ الملفات. فإن كان عملك يتطلب الكتابة، فستحتاج إلى البحث في مكان آخر. وتذكّر أن تواصل التفكير فيما توفره المكتبة القياسية حالياً، فإن كنت تكتب بيانات فعليك على الأرجح الاستفادة من الواجهات الموجودة مثل `io.Writer` لتبقى شيفرتك ضعيفة الاقتران وقابلة لإعادة الاستعمال.

### قراءات إضافية

- كان هذا مدخلاً خفيفاً إلى `io/fs`. [وقد كتب بن كونغدون مقالاً ممتازاً](https://benjamincongdon.me/blog/2021/01/21/A-Tour-of-Go-116s-iofs-package/) ساعدني كثيراً في كتابة هذا الفصل.
- [نقاش حول واجهات نظام الملفات](https://github.com/golang/go/issues/41190)
