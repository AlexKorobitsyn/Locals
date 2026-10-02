export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public field_errors: string[] = [],
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

const STATUS_MESSAGES: Record<number, string> = {
  401: 'Нужно войти в аккаунт. Если вы уже вошли, сессия истекла.',
  403: 'У вас нет прав для этого действия.',
  404: 'Не найдено или недоступно для этого аккаунта.',
  409: 'Данные изменились или такая запись уже существует. Обновите страницу.',
  413: 'Файл превышает разрешённый размер.',
  415: 'Этот формат файла не поддерживается.',
  422: 'Проверьте заполненные поля.',
  503: 'Сервис временно недоступен. Попробуйте ещё раз.',
};
const DETAIL_MESSAGES: Record<string, string> = {
  'Pending contribution limit reached; wait for existing proposals to be reviewed':
    'Вы достигли лимита открытых предложений. Дождитесь принятия или отзовите старые.',
  'Active event limit reached': 'Достигнут лимит будущих событий вашего уровня.',
  "This field contains the owner's authoritative version; owner approval required":
    'У этой записи есть версия владельца. Правку должен одобрить сам владелец.',
  'Content changed since submission; submit a fresh proposal':
    'Запись уже изменилась. Отзовите предложение и отправьте новое.',
  'You already have a pending proposal for this field':
    'У вас уже есть открытое предложение для этого поля.',
  'Withdraw the pending proposal and create a corrected one':
    'Отзовите предложение в разделе сообщества и создайте исправленное.',
  'All winners for this period have already been selected':
    'Победители за этот период уже выбраны.',
  'Weekly award period must be a Monday': 'Для недельной награды выберите понедельник.',
  'Monthly award period must be the first day': 'Для месячной награды выберите первое число.',
  'Remove dependent events before withdrawing the venue':
    'Сначала отзовите события на этой площадке.',

  'Browser origin is not allowed':
    'Вход недоступен по этому адресу сайта. Обратитесь к администратору.',
  'File is empty': 'Файл пустой. Выберите другой.',
  'Invalid image content': 'Изображение повреждено или его содержимое не соответствует формату.',
  'Invalid audio content': 'Аудиофайл повреждён или его содержимое не соответствует формату.',
  'Only static JPEG, PNG and WebP are supported':
    'Для обложки подходят статичные JPEG, PNG и WebP.',
  'Only MP3, FLAC and WAV are supported': 'Для аудио подходят MP3, FLAC и WAV.',
  'Image dimensions exceed the limit':
    'Слишком большое разрешение изображения. Уменьшите его и попробуйте снова.',
  'At least one artist is required': 'Добавьте хотя бы одного своего артиста.',
  'Email already registered': 'Этот email уже зарегистрирован.',
  'Invalid or expired credentials': 'Неверные данные входа или сессия истекла.',
  'Track audio not found': 'У этого трека пока нет аудио.',
  'Object storage is not configured': 'Аудиохранилище пока недоступно.',
  'Set a rating before writing a review': 'Сначала оцените музыку, затем напишите рецензию.',
  'Review already exists': 'Ваша рецензия уже существует.',
  'Track already in playlist': 'Этот трек уже есть в плейлисте.',
  'Reorder must include every current track exactly once':
    'Порядок изменился. Полный список треков загружен заново.',
};
const FIELD_NAMES: Record<string, string> = {
  email: 'Email',
  password: 'Пароль',
  display_name: 'Имя',
  text: 'Текст',
  title: 'Название',
  name: 'Название',
  value: 'Оценка',
  genre_ids: 'Жанры',
  city_id: 'Город',
  venue_id: 'Площадка',
  lat: 'Широта',
  lng: 'Долгота',
  artist_ids: 'Артисты',
  artist_credits: 'Участники записи',
  starts_at: 'Начало',
  stop_at: 'Окончание',
  type_event_ids: 'Тип события',
  website: 'Сайт',
  capacity: 'Вместимость',
};

export function response_error(status: number, body: unknown): ApiError {
  const detail = body && typeof body === 'object' && 'detail' in body ? body.detail : undefined;
  const message =
    (typeof detail === 'string' && DETAIL_MESSAGES[detail]) ||
    STATUS_MESSAGES[status] ||
    'Не удалось выполнить запрос. Попробуйте ещё раз.';
  const field_errors = Array.isArray(detail)
    ? detail.map((item: unknown) => {
        if (!item || typeof item !== 'object' || !('loc' in item) || !Array.isArray(item.loc))
          return 'Некорректное поле';
        const field = String(item.loc.at(-1));
        return `${FIELD_NAMES[field] || field}: недопустимое значение`;
      })
    : [];
  return new ApiError(status, message, field_errors);
}

export function error_message(error: unknown) {
  return error instanceof ApiError
    ? error.message
    : 'Не удалось связаться с сервером. Проверьте соединение и повторите запрос.';
}
