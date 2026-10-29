# عودة إلى معالجات HTTP

**[تجد كل الشيفرة هنا](https://github.com/quii/learn-go-with-tests/tree/main/q-and-a/http-handlers-revisited)**

في هذا الكتاب فصل بالفعل عن [اختبار معالج HTTP](http-server.md)، لكن هذا الفصل سيتضمن نقاشاً أوسع حول تصميمها، بحيث تكون بسيطة الاختبار.

سننظر في مثال حقيقي، وفي كيفية تحسين تصميمه بتطبيق مبادئ مثل مبدأ المسؤولية الواحدة وفصل الاهتمامات. ويمكن تحقيق هذه المبادئ باستعمال [الواجهات](structs-methods-and-interfaces.md) و[حقن التبعية](dependency-injection.md). وبفعل ذلك سنبيّن أن اختبار المعالجات (handlers) بسيط جداً في الحقيقة.

![سؤال شائع في مجتمع غو في صورة](amazing-art.png)

يبدو أن اختبار معالجات HTTP سؤال متكرر في مجتمع غو (Go)، وأظن أنه يشير إلى مشكلة أوسع، وهي سوء فهم الناس لكيفية تصميمها.

فكثيراً ما تنبع صعوبات الناس في الاختبار من تصميم شيفرتهم (code)، لا من كتابة الاختبارات نفسها. وكما أشدد كثيراً في هذا الكتاب:

> إن كانت اختباراتك تسبب لك الألم، فأصغِ إلى تلك الإشارة وفكّر في تصميم شيفرتك.

## مثال

[غرّد لي سانتوش كومار](https://twitter.com/sntshk/status/1255559003339284481)

> كيف أختبر معالج HTTP له تبعية على قاعدة بيانات mongodb الخاصة بي؟

إليك الشيفرة

```go
func Registration(w http.ResponseWriter, r *http.Request) {
	var res model.ResponseResult
	var user model.User

	w.Header().Set("Content-Type", "application/json")

	jsonDecoder := json.NewDecoder(r.Body)
	jsonDecoder.DisallowUnknownFields()
	defer r.Body.Close()

	// check if there is proper json body or error
	if err := jsonDecoder.Decode(&user); err != nil {
		res.Error = err.Error()
		// return 400 status codes
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(res)
		return
	}

	// Connect to mongodb
	client, _ := mongo.NewClient(options.Client().ApplyURI("mongodb://127.0.0.1:27017"))
	ctx, _ := context.WithTimeout(context.Background(), 10*time.Second)
	err := client.Connect(ctx)
	if err != nil {
		panic(err)
	}
	defer client.Disconnect(ctx)
	// Check if username already exists in users datastore, if so, 400
	// else insert user right away
	collection := client.Database("test").Collection("users")
	filter := bson.D{{"username", user.Username}}
	var foundUser model.User
	err = collection.FindOne(context.TODO(), filter).Decode(&foundUser)
	if foundUser.Username == user.Username {
		res.Error = UserExists
		// return 400 status codes
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(res)
		return
	}

	pass, err := bcrypt.GenerateFromPassword([]byte(user.Password), bcrypt.DefaultCost)
	if err != nil {
		res.Error = err.Error()
		// return 400 status codes
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(res)
		return
	}
	user.Password = string(pass)

	insertResult, err := collection.InsertOne(context.TODO(), user)
	if err != nil {
		res.Error = err.Error()
		// return 400 status codes
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(res)
		return
	}

	// return 200
	w.WriteHeader(http.StatusOK)
	res.Result = fmt.Sprintf("%s: %s", UserCreated, insertResult.InsertedID)
	json.NewEncoder(w).Encode(res)
	return
}
```

لنسرد فقط كل الأشياء التي على هذه الدالة (function) الواحدة فعلها:

1. كتابة استجابات HTTP، وإرسال الترويسات ورموز الحالة وغيرها.
2. فك ترميز متن الطلب إلى `User`
3. الاتصال بقاعدة بيانات (وكل التفاصيل المتعلقة بذلك)
4. الاستعلام من قاعدة البيانات وتطبيق بعض منطق الأعمال بحسب النتيجة
5. توليد كلمة مرور
6. إدراج سجل

هذا أكثر من اللازم.

## ما معالج HTTP، وما الذي ينبغي أن يفعله؟

بنسيان تفاصيل غو المحددة للحظة، أياً كانت اللغة التي عملت بها، فما خدمني دائماً جيداً هو التفكير في [فصل الاهتمامات](https://en.wikipedia.org/wiki/Separation_of_concerns) و[مبدأ المسؤولية الواحدة](https://en.wikipedia.org/wiki/Single-responsibility_principle).

وقد يكون تطبيق هذا صعباً بعض الشيء بحسب المشكلة التي تحلها. فما هي المسؤولية بالضبط؟

قد تتداخل الحدود بحسب مدى تجريد تفكيرك، وقد لا يكون تخمينك الأول صحيحاً أحياناً.

لحسن الحظ، مع معالجات HTTP أشعر أن لدي فكرة جيدة جداً عما ينبغي أن تفعله، أياً كان المشروع الذي عملت عليه:

1. قبول طلب HTTP، وتحليله والتحقق من صحته.
2. استدعاء `ServiceThing` ما لتنفيذ `ImportantBusinessLogic` بالبيانات التي حصلت عليها من الخطوة 1.
3. إرسال استجابة `HTTP` مناسبة بحسب ما يعيده `ServiceThing`.

لا أقول إن كل معالج HTTP على _الإطلاق_ ينبغي أن يكون له هذا الشكل تقريباً، لكن هذا يبدو الحال لدي في 99 مرة من 100.

حين تفصل هذه الاهتمامات:

 - يصبح اختبار المعالجات يسيراً، ويركز على عدد صغير من الاهتمامات.
 - والأهم أن اختبار `ImportantBusinessLogic` لم يعد يحتاج إلى الاهتمام بـ`HTTP`، فيمكنك اختبار منطق الأعمال بنظافة.
 - يمكنك استعمال `ImportantBusinessLogic` في سياقات أخرى دون الحاجة إلى تعديلها.
 - وإن غيّرت `ImportantBusinessLogic` ما تفعله، فما دامت الواجهة (interface) باقية كما هي فلا تحتاج إلى تغيير معالجاتك.

## المعالجات في غو

النوع [`http.HandlerFunc`](https://golang.org/pkg/net/http/#HandlerFunc)

> النوع `HandlerFunc` محوّل يتيح استعمال الدوال العادية معالجاتٍ لطلبات HTTP الواردة.

`type HandlerFunc func(ResponseWriter, *Request)`

أيها القارئ، خذ نفساً وانظر إلى الشيفرة أعلاه. ماذا تلاحظ؟

**إنها دالة تأخذ بعض الوسطاء**

لا سحر إطار عمل، ولا تعليقات توضيحية، ولا حبوب سحرية، لا شيء.

إنها مجرد دالة، _ونحن نعرف كيف نختبر الدوال_.

وهي تنسجم جيداً مع التعليق أعلاه:

- تأخذ [`http.Request`](https://golang.org/pkg/net/http/#Request)، وهو مجرد حزمة من البيانات نفحصها ونحللها ونتحقق من صحتها.
- > [تستعمل معالجات HTTP الواجهة `http.ResponseWriter` لبناء استجاباتها.](https://golang.org/pkg/net/http/#ResponseWriter)

### مثال اختبار بسيط جداً

```go
func Teapot(res http.ResponseWriter, req *http.Request) {
	res.WriteHeader(http.StatusTeapot)
}

func TestTeapotHandler(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	res := httptest.NewRecorder()

	Teapot(res, req)

	if res.Code != http.StatusTeapot {
		t.Errorf("got status %d but wanted %d", res.Code, http.StatusTeapot)
	}
}
```

لاختبار دالتنا، _نستدعيها_.

في اختبارنا (test) نمرر `httptest.ResponseRecorder` كوسيط `http.ResponseWriter`، وستستعمله دالتنا لكتابة استجابة `HTTP`. وسيسجّل المسجِّل (أو _يتجسس_ على) ما أُرسل، ثم يمكننا إجراء توكيداتنا (assertions).

## استدعاء `ServiceThing` في معالجنا

من الشكاوى الشائعة على دروس `TDD` أنها دائماً "بسيطة أكثر من اللازم" وليست "واقعية بما يكفي". وجوابي على ذلك:

> ألن يكون جميلاً لو كانت كل شيفرتك بسيطة القراءة والاختبار كالأمثلة التي تذكرها؟

هذا من أكبر التحديات التي نواجهها، لكن علينا مواصلة السعي إليه. فمن _الممكن_ (وإن لم يكن سهلاً بالضرورة) تصميم الشيفرة بحيث تكون بسيطة القراءة والاختبار، إن مارسنا وطبّقنا مبادئ جيدة في هندسة البرمجيات.

تذكيراً بما يفعله المعالج السابق:

1. كتابة استجابات HTTP، وإرسال الترويسات ورموز الحالة وغيرها.
2. فك ترميز متن الطلب إلى `User`
3. الاتصال بقاعدة بيانات (وكل التفاصيل المتعلقة بذلك)
4. الاستعلام من قاعدة البيانات وتطبيق بعض منطق الأعمال بحسب النتيجة
5. توليد كلمة مرور
6. إدراج سجل

بأخذ فكرة فصل أمثل للاهتمامات، أريده أن يكون أقرب إلى:

1. فك ترميز متن الطلب إلى `User`
2. استدعاء `UserService.Register(user)` (وهذا هو `ServiceThing` لدينا)
3. إن كان هناك خطأ فالتصرف بناءً عليه (المثال يرسل دائماً `400 BadRequest`، ولا أظن ذلك صحيحاً)، وسأكتفي _في الوقت الحالي_ بمعالج شامل يعيد `500 Internal Server Error`. ولا بد أن أشدد على أن إعادة `500` لكل الأخطاء تصنع واجهة برمجية فظيعة! ويمكننا لاحقاً جعل معالجة الأخطاء أكثر تطوراً، ربما بـ[أنواع الأخطاء](error-types.md).
4. إن لم يكن هناك خطأ، فإعادة `201 Created` مع المعرّف في متن الاستجابة (مرة أخرى، للاختصار أو الكسل)

اختصاراً، لن أمر بعملية `TDD` المعتادة، فراجع كل الفصول الأخرى للأمثلة.

### التصميم الجديد

```go
type UserService interface {
	Register(user User) (insertedID string, err error)
}

type UserServer struct {
	service UserService
}

func NewUserServer(service UserService) *UserServer {
	return &UserServer{service: service}
}

func (u *UserServer) RegisterUser(w http.ResponseWriter, r *http.Request) {
	defer r.Body.Close()

	// request parsing and validation
	var newUser User
	err := json.NewDecoder(r.Body).Decode(&newUser)

	if err != nil {
		http.Error(w, fmt.Sprintf("could not decode user payload: %v", err), http.StatusBadRequest)
		return
	}

	// call a service thing to take care of the hard work
	insertedID, err := u.service.Register(newUser)

	// depending on what we get back, respond accordingly
	if err != nil {
		//todo: handle different kinds of errors differently
		http.Error(w, fmt.Sprintf("problem registering new user: %v", err), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	fmt.Fprint(w, insertedID)
}
```

تطابق الطريقة (method) `RegisterUser` شكل `http.HandlerFunc`، لذا نحن جاهزون. وقد أرفقناها كطريقة على نوع (type) جديد هو `UserServer`، يحتوي على تبعية على `UserService` مجسّدة كواجهة.

الواجهات وسيلة رائعة لضمان أن اهتمامات `HTTP` لدينا منفصلة عن أي تنفيذ محدد؛ فيمكننا ببساطة استدعاء الطريقة على التبعية، ولا نحتاج إلى الاهتمام بـ_كيفية_ تسجيل المستخدم.

إن أردت استكشاف هذا الأسلوب بتفصيل أكبر مع اتباع `TDD`، فاقرأ فصل [حقن التبعية](dependency-injection.md) و[فصل خادم HTTP في قسم "بناء تطبيق"](http-server.md).

والآن بعد أن فككنا الاقتران عن أي تفاصيل تنفيذ محددة حول التسجيل، صارت كتابة شيفرة معالجنا مباشرة، وتتبع المسؤوليات الموصوفة سابقاً.

### الاختبارات!

تنعكس هذه البساطة في اختباراتنا.

```go
type MockUserService struct {
	RegisterFunc    func(user User) (string, error)
	UsersRegistered []User
}

func (m *MockUserService) Register(user User) (insertedID string, err error) {
	m.UsersRegistered = append(m.UsersRegistered, user)
	return m.RegisterFunc(user)
}

func TestRegisterUser(t *testing.T) {
	t.Run("can register valid users", func(t *testing.T) {
		user := User{Name: "CJ"}
		expectedInsertedID := "whatever"

		service := &MockUserService{
			RegisterFunc: func(user User) (string, error) {
				return expectedInsertedID, nil
			},
		}
		server := NewUserServer(service)

		req := httptest.NewRequest(http.MethodGet, "/", userToJSON(user))
		res := httptest.NewRecorder()

		server.RegisterUser(res, req)

		assertStatus(t, res.Code, http.StatusCreated)

		if res.Body.String() != expectedInsertedID {
			t.Errorf("expected body of %q but got %q", res.Body.String(), expectedInsertedID)
		}

		if len(service.UsersRegistered) != 1 {
			t.Fatalf("expected 1 user added but got %d", len(service.UsersRegistered))
		}

		if !reflect.DeepEqual(service.UsersRegistered[0], user) {
			t.Errorf("the user registered %+v was not what was expected %+v", service.UsersRegistered[0], user)
		}
	})

	t.Run("returns 400 bad request if body is not valid user JSON", func(t *testing.T) {
		server := NewUserServer(nil)

		req := httptest.NewRequest(http.MethodGet, "/", strings.NewReader("trouble will find me"))
		res := httptest.NewRecorder()

		server.RegisterUser(res, req)

		assertStatus(t, res.Code, http.StatusBadRequest)
	})

	t.Run("returns a 500 internal server error if the service fails", func(t *testing.T) {
		user := User{Name: "CJ"}

		service := &MockUserService{
			RegisterFunc: func(user User) (string, error) {
				return "", errors.New("couldn't add new user")
			},
		}
		server := NewUserServer(service)

		req := httptest.NewRequest(http.MethodGet, "/", userToJSON(user))
		res := httptest.NewRecorder()

		server.RegisterUser(res, req)

		assertStatus(t, res.Code, http.StatusInternalServerError)
	})
}
```

والآن بعد أن لم يعد معالجنا مقترناً بتنفيذ محدد للتخزين، صار من البسيط علينا كتابة `MockUserService` يساعدنا على كتابة اختبارات وحدة بسيطة وسريعة تختبر مسؤولياته المحددة.

### وماذا عن شيفرة قاعدة البيانات؟ أنت تغش!

هذا كله مقصود تماماً. فلا نريد أن تهتم معالجات HTTP بمنطق أعمالنا وقواعد البيانات والاتصالات وغير ذلك.

بفعل هذا حررنا المعالج من التفاصيل الفوضوية، وجعلنا _أيضاً_ اختبار طبقة التخزين الدائم ومنطق الأعمال أسهل، لأنهما لم يعودا مقترنين بتفاصيل HTTP غير ذات الصلة.

كل ما علينا فعله الآن هو تنفيذ `UserService` باستعمال أي قاعدة بيانات نريدها

```go
type MongoUserService struct {
}

func NewMongoUserService() *MongoUserService {
	//todo: pass in DB URL as argument to this function
	//todo: connect to db, create a connection pool
	return &MongoUserService{}
}

func (m MongoUserService) Register(user User) (insertedID string, err error) {
	// use m.mongoConnection to perform queries
	panic("implement me")
}
```

يمكننا اختبار هذا منفصلاً، وبمجرد أن نرضى، يمكننا في `main` تركيب هاتين الوحدتين معاً للحصول على تطبيقنا العامل.

```go
func main() {
	mongoService := NewMongoUserService()
	server := NewUserServer(mongoService)
	http.ListenAndServe(":8000", http.HandlerFunc(server.RegisterUser))
}
```

### تصميم أكثر متانة وقابلية للتوسيع بجهد قليل

لا تسهّل هذه المبادئ حياتنا على المدى القصير فحسب، بل تجعل النظام أسهل في التوسيع مستقبلاً.

لن يكون مفاجئاً أن نريد في تكرارات لاحقة لهذا النظام إرسال بريد إلكتروني إلى المستخدم لتأكيد التسجيل.

مع التصميم القديم كنا سنضطر إلى تغيير المعالج _و_ الاختبارات المحيطة به. وهكذا كثيراً ما تصبح أجزاء من الشيفرة غير قابلة للصيانة، إذ تتسلل إليها وظائف أكثر فأكثر لأنها _مصممة_ بالفعل بهذه الطريقة؛ ليعالج "معالج HTTP"... كل شيء!

بفصل الاهتمامات باستعمال واجهة، لا نحتاج إلى تعديل المعالج _إطلاقاً_، لأنه لا يهتم بمنطق الأعمال المتعلق بالتسجيل.

## الخلاصة

اختبار معالجات HTTP في غو ليس صعباً، لكن تصميم برمجيات جيدة قد يكون كذلك!

يخطئ الناس حين يظنون أن معالجات HTTP خاصة، فيتخلون عن الممارسات الجيدة في هندسة البرمجيات حين يكتبونها، فيصبح اختبارها صعباً.

وللتكرار مرة أخرى: **معالجات HTTP في غو ليست إلا دوالاً**. فإن كتبتها كما تكتب الدوال الأخرى، بمسؤوليات واضحة وفصل جيد للاهتمامات، فلن تجد أي صعوبة في اختبارها، وستكون قاعدة شيفرتك أكثر صحة بفضل ذلك.
