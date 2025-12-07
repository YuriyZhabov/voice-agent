# 📋 IMPLEMENTATION ROADMAP: Voice Agent Platform
## Пошаговый план разработки для инженеров

**Версия**: 1.0  
**Дата**: Декабрь 2025  
**Статус**: Ready for development team  
**Целевой выпуск**: Q1 2026  

---

## 📍 EXECUTIVE SUMMARY

Этот документ содержит **детальный plan разработки** на основе architecture design document.

- **🕐 Общее время**: 16 недель (4 месяца) для MVP
- **👥 Рекомендуемая team**: 4-5 инженеров (backend/frontend/DevOps)
- **📊 5 фаз разработки**: Foundation → Core → Advanced → Polish → Hardening
- **🎯 Каждый спринт**: 2 недели с четкими deliverables

---

## 🏗️ PHASE 1: FOUNDATION (Weeks 1-2)

### Цель
Создать базовую инфраструктуру и auth систему.

### Sprint 1.1: Infrastructure Setup (Week 1)

#### Задачи:

**1.1.1 Cloud Setup & DevOps**
- [ ] AWS/GCP аккаунт и базовая конфигурация
- [ ] Neon PostgreSQL инстанс + backup policy
- [ ] Redis инстанс (AWS ElastiCache или Upstash)
- [ ] S3 bucket для recording'ов с шифрованием KMS
- [ ] Terraform/IaC для управления инфраструктурой
- [ ] CI/CD pipeline (GitHub Actions или GitLab CI)
  - [ ] Lint, format, type check
  - [ ] Unit tests на каждый коммит
  - [ ] Build Docker images
  - [ ] Deploy to staging автоматически

**Deliverables:**
```
- terraform/ directory with cloud resources
- docker-compose.yml для локальной разработки
- .github/workflows/ для CI/CD
- Staging environment доступное на https://staging.voiceagent.app
```

**Effort**: 40 hours (1 DevOps engineer)

---

**1.1.2 Database Schema v1 (Basic)**
- [ ] PostgreSQL migration system (Flyway или Alembic)
- [ ] Таблицы Phase 1:
  ```sql
  ✅ organizations
  ✅ users
  ✅ api_keys
  ✅ sessions
  ```
- [ ] Row Level Security (RLS) для multi-tenancy
- [ ] Индексы для основных запросов
- [ ] Backup automation (daily snapshots)

**Deliverables:**
```
migrations/
├── 001_initial_schema.sql
├── 002_rls_policies.sql
└── 003_indexes.sql

.env.example с подсказками
```

**Effort**: 16 hours

---

**1.1.3 API Gateway & Auth Framework**
- [ ] Express/Fastify server setup
- [ ] TLS/HTTPS configuration
- [ ] CORS middleware
- [ ] Request logging & OpenTelemetry setup
- [ ] Error handling middleware
- [ ] Rate limiting middleware (token bucket, Redis-backed)

**Code structure:**
```
src/
├── middleware/
│   ├── auth.ts          # JWT/API Key validation
│   ├── rateLimit.ts     # Rate limiter
│   ├── cors.ts
│   └── errors.ts
├── utils/
│   └── logger.ts        # Structured logging
└── server.ts            # Express setup
```

**Deliverables:**
- [ ] Server запускается на http://localhost:3000
- [ ] Health check endpoint: `GET /health`
- [ ] Basic error responses с proper HTTP codes

**Effort**: 24 hours

---

### Sprint 1.2: Authentication & User Management (Week 2)

#### Задачи:

**1.2.1 User Registration & Email Verification**

```typescript
// Key interfaces to implement:
interface RegisterRequest {
  email: string;
  password: string;
  organizationName: string;
}

interface RegisterResponse {
  userId: string;
  organizationId: string;
  verificationEmailSent: boolean;
}

interface VerifyEmailRequest {
  token: string;  // from email link
}
```

- [ ] POST /auth/register endpoint
- [ ] Email service integration (SendGrid или Resend)
- [ ] Email verification token (JWT, 24h expiry)
- [ ] Password hashing (bcrypt with salt)
- [ ] Default organization creation при регистрации
- [ ] Tests для всех сценариев

**Deliverables:**
- [ ] User registration работает
- [ ] Email verification работает
- [ ] Verified & unverified пользователи имеют разные permissions

**Effort**: 32 hours

---

**1.2.2 JWT Authentication & Sessions**

- [ ] JWT token generation (access + refresh)
- [ ] POST /auth/login endpoint
- [ ] POST /auth/logout endpoint
- [ ] POST /auth/refresh-token endpoint
- [ ] JWT payload structure:
  ```json
  {
    "userId": "...",
    "organizationId": "...",
    "email": "...",
    "role": "admin|agent|viewer",
    "iat": 1234567890,
    "exp": 1234571490
  }
  ```
- [ ] Session management (optional, для tracking active sessions)

**Deliverables:**
- [ ] Login работает
- [ ] Token refresh работает
- [ ] Protected endpoints требуют валидный JWT

**Effort**: 28 hours

---

**1.2.3 API Key Management**

```typescript
interface APIKey {
  id: string;
  keyHash: string;        // SHA-256
  name: string;
  scopes: string[];       // e.g., ["read:calls", "write:agents"]
  lastUsedAt: Date | null;
  createdAt: Date;
  expiresAt?: Date;
}

interface CreateAPIKeyRequest {
  name: string;
  scopes: string[];
  expiresInDays?: number;
}

interface CreateAPIKeyResponse {
  key: string;            // Only shown once!
  keyId: string;
}
```

- [ ] POST /api-keys (create)
- [ ] GET /api-keys (list)
- [ ] DELETE /api-keys/:id (revoke)
- [ ] API Key authentication (X-API-Key header)
- [ ] Scopes/permissions system
- [ ] Security: Never log full keys, hash before storage

**Deliverables:**
- [ ] API Keys работают как альтернатива JWT
- [ ] Scopes enforced в handlers
- [ ] /health endpoint работает как с JWT так и с API Key

**Effort**: 32 hours

---

**1.2.4 Testing & Documentation**

- [ ] Unit tests для auth (jest/vitest)
- [ ] Integration tests для endpoints (supertest)
- [ ] OpenAPI/Swagger documentation
- [ ] Postman collection для manual testing

**Deliverables:**
```
npm test -- auth/    # ✅ все тесты проходят

docs/
├── API.md           # OpenAPI 3.0 spec
├── AUTH.md          # Auth flow diagrams
└── POSTMAN.json     # Постман коллекция
```

**Effort**: 24 hours

---

### ✅ Phase 1 Summary

| Компонент | Статус | Time | Owner |
|-----------|--------|------|-------|
| Infrastructure | Done ✅ | 40h | DevOps |
| Database Schema | Done ✅ | 16h | Backend |
| API Gateway | Done ✅ | 24h | Backend |
| Auth System | Done ✅ | 92h | Backend |
| **TOTAL** | | **172h** | 2-3 people |

**Milestone**: Два инженера могут успешно регистрироваться и авторизоваться.

---

## 🎙️ PHASE 2: CORE CALL FUNCTIONALITY (Weeks 3-6)

### Цель
Реализовать основной flow: звонки → агенты → LLM → TTS.

### Sprint 2.1: Call Management Service (Week 3)

#### Database Schema Update:

```sql
-- Add tables needed for Phase 2
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    owner_id UUID,
    plan VARCHAR(50),
    status VARCHAR(50),
    created_at TIMESTAMP,
    metadata JSONB
);

CREATE TABLE agents (
    id UUID PRIMARY KEY,
    org_id UUID,
    name VARCHAR(255),
    system_prompt TEXT,
    llm_model VARCHAR(100),
    voice_id VARCHAR(100),
    status VARCHAR(50),
    version INT,
    created_at TIMESTAMP
);

CREATE TABLE phone_numbers (
    id UUID PRIMARY KEY,
    org_id UUID,
    agent_id UUID,
    number VARCHAR(20),
    status VARCHAR(50),
    created_at TIMESTAMP
);

CREATE TABLE calls (
    id UUID PRIMARY KEY,
    org_id UUID,
    agent_id UUID,
    from_number VARCHAR(20),
    to_number VARCHAR(20),
    direction VARCHAR(20),
    status VARCHAR(50),
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INT,
    recording_url VARCHAR(500),
    cost_kopecks NUMERIC,
    created_at TIMESTAMP
);

CREATE INDEX calls_org_id ON calls(org_id);
CREATE INDEX calls_agent_id ON calls(agent_id);
```

**Effort**: 12 hours

---

#### Задачи:

**2.1.1 Agent CRUD API**

```typescript
// POST /agents
interface CreateAgentRequest {
  name: string;
  system_prompt: string;
  llm_model: 'gpt-4o-mini' | 'claude-3-5-sonnet';
  llm_temperature: number;    // 0-1
  llm_max_tokens: number;     // 1-4096
  voice_id: string;           // 'alex', 'maya', etc
}

interface Agent {
  id: string;
  name: string;
  system_prompt: string;
  llm_config: { model, temperature, max_tokens };
  voice_id: string;
  status: 'draft' | 'published' | 'archived';
  version: number;
  created_at: Date;
  updated_at: Date;
}
```

- [ ] POST /agents (create)
- [ ] GET /agents (list for org)
- [ ] GET /agents/:id (get one)
- [ ] PATCH /agents/:id (update)
- [ ] DELETE /agents/:id (soft delete)
- [ ] Input validation (prompt length, model names, etc)
- [ ] Version control (each update increments version)
- [ ] Tests

**Effort**: 32 hours

---

**2.1.2 Phone Number Management**

```typescript
// POST /phone-numbers
interface AddPhoneNumberRequest {
  number: string;             // E.164 format: +7XXXXXXXXXX
  agent_id: string;
}

interface PhoneNumber {
  id: string;
  org_id: string;
  agent_id: string;
  number: string;
  sip_trunk_id?: string;
  status: 'active' | 'inactive';
  created_at: Date;
}
```

- [ ] POST /phone-numbers (add)
- [ ] GET /phone-numbers (list)
- [ ] DELETE /phone-numbers/:id (remove)
- [ ] E.164 format validation
- [ ] Integration with MTS Exolve (stub for now, real integration in Phase 3)

**Effort**: 20 hours

---

**2.1.3 Call History API**

```typescript
// GET /calls
interface CallListRequest {
  page: number;
  limit: number;
  agent_id?: string;
  status?: CallStatus;
  from_date?: Date;
  to_date?: Date;
}

interface CallListResponse {
  calls: Call[];
  total: number;
  page: number;
  pages: number;
}
```

- [ ] GET /calls (list with filters)
- [ ] GET /calls/:id (get one)
- [ ] GET /calls/:id/transcript (get conversation)
- [ ] Pagination support
- [ ] Filtering by agent, date range, status
- [ ] Tests

**Effort**: 24 hours

---

**2.1.4 WebSocket Setup для Real-Time Updates**

- [ ] WebSocket server (ws или Socket.io)
- [ ] Connection auth (use JWT)
- [ ] Event broadcasting:
  - `call:initiated`
  - `call:connected`
  - `call:ended`
- [ ] Connection management (cleanup on disconnect)

**Effort**: 20 hours

---

### Sprint 2.2: LLM Integration & Streaming (Week 4)

#### Задачи:

**2.2.1 LLM Router Implementation (Python service)**

```python
# New Python service: agent-orchestrator
# Can be run as separate microservice или embedded

from typing import AsyncIterator
import asyncio

class LLMRouter:
    """Multi-tier LLM fallback with circuit breaker"""
    
    def __init__(self):
        self.openai = OpenAIClient(...)
        self.claude = AnthropicClient(...)
        self.llama = LocalLlamaClient(...)
        
        self.circuit_breakers = {
            "openai": CircuitBreaker(failures=5, timeout=30),
            "claude": CircuitBreaker(failures=5, timeout=30),
            "llama": CircuitBreaker(failures=5, timeout=15),
        }
    
    async def get_response(
        self, 
        prompt: str, 
        attempt: int = 0
    ) -> str:
        """Get response with automatic fallback"""
        
        models = [
            ("openai", self.openai, 30),
            ("claude", self.claude, 30),
            ("llama", self.llama, 15),
        ]
        
        for model_name, client, timeout in models[attempt:]:
            if self.circuit_breakers[model_name].is_open():
                logger.info(f"Circuit breaker open for {model_name}")
                continue
            
            try:
                response = await asyncio.wait_for(
                    client.chat(prompt),
                    timeout=timeout
                )
                self.circuit_breakers[model_name].record_success()
                logger.info(f"✅ {model_name} success")
                return response
            
            except asyncio.TimeoutError:
                self.circuit_breakers[model_name].record_failure()
                logger.warning(f"⏱ {model_name} timeout")
                if attempt < len(models) - 1:
                    return await self.get_response(prompt, attempt + 1)
            
            except Exception as e:
                self.circuit_breakers[model_name].record_failure()
                logger.error(f"❌ {model_name}: {e}")
                if attempt < len(models) - 1:
                    return await self.get_response(prompt, attempt + 1)
        
        # All failed - fallback
        return "Временно недоступно, попробуйте позже"
```

- [ ] Circuit breaker implementation
- [ ] OpenAI integration (test with gpt-4o-mini)
- [ ] Claude integration (test with claude-3-5-sonnet)
- [ ] Local Llama setup (with GPU support)
- [ ] Tests for each fallback scenario

**Setup:**
```
# requirements.txt
openai==1.3.0
anthropic==0.7.0
fastapi==0.104.0
pydantic==2.0.0
```

**Effort**: 40 hours

---

**2.2.2 TTS Integration with Fallback**

```python
class TTSRouter:
    """Multi-tier TTS with fallback"""
    
    async def synthesize(self, text: str) -> AsyncIterator[bytes]:
        """Stream audio with automatic fallback"""
        
        services = [
            ("elevenlabs", self.elevenlabs_client, 10),
            ("google_tts", self.google_tts_client, 10),
            ("aws_polly", self.aws_polly_client, 10),
        ]
        
        for name, client, timeout in services:
            try:
                async for chunk in asyncio.wait_for(
                    client.stream(text),
                    timeout=timeout
                ):
                    yield chunk
                logger.info(f"✅ TTS via {name}")
                return
            except Exception as e:
                logger.warning(f"TTS {name} failed: {e}")
                continue
        
        # All TTS failed - use pre-recorded fallback
        logger.error("All TTS services failed, using fallback")
        yield self.get_prerecorded_fallback("service_unavailable")
```

- [ ] ElevenLabs integration
- [ ] Google Cloud TTS fallback
- [ ] AWS Polly fallback
- [ ] Pre-recorded fallback messages
- [ ] Audio streaming (send chunks as they arrive)

**Effort**: 32 hours

---

**2.2.3 STT Integration (Deepgram) with Confidence Threshold**

```python
class STTRouter:
    """STT with confidence threshold and fallback"""
    
    MIN_CONFIDENCE = 0.60  # 60%
    MAX_RETRIES = 3
    
    async def transcribe(
        self, 
        audio_stream: AsyncIterator[bytes]
    ) -> TranscriptionResult:
        """Transcribe with confidence checks"""
        
        services = [
            ("deepgram", self.deepgram_client, 10),
            ("google_speech", self.google_speech_client, 10),
        ]
        
        for name, client, timeout in services:
            try:
                result = await asyncio.wait_for(
                    client.transcribe(audio_stream),
                    timeout=timeout
                )
                
                if result.confidence >= self.MIN_CONFIDENCE:
                    logger.info(f"✅ STT: {result.text} ({result.confidence:.2%})")
                    return result
                else:
                    logger.warning(f"Low confidence: {result.confidence:.2%}")
                    return TranscriptionResult(
                        text="",
                        confidence=0,
                        needs_retry=True,
                        message="Не услышал хорошо, повторите пожалуйста"
                    )
            
            except Exception as e:
                logger.warning(f"STT {name} failed: {e}")
                continue
        
        # All failed
        return TranscriptionResult(
            text="",
            confidence=0,
            needs_retry=True,
            message="Проблемы со связью"
        )

@dataclass
class TranscriptionResult:
    text: str
    confidence: float
    needs_retry: bool
    message: str = ""
```

- [ ] Deepgram WebSocket connection
- [ ] Confidence threshold (60%)
- [ ] Google Speech-to-Text fallback
- [ ] Retry logic

**Effort**: 28 hours

---

**2.2.4 Streaming Pipeline (LLM + TTS Parallel)**

```python
async def stream_agent_response(
    self, 
    user_text: str,
    context: ConversationContext
) -> AsyncIterator[bytes]:
    """
    Stream LLM tokens DIRECTLY to TTS
    This achieves <300ms perceived latency
    """
    
    llm_stream = self.llm_router.stream_tokens(
        self._build_prompt(user_text, context)
    )
    
    tts_queue = asyncio.Queue(maxsize=10)
    
    async def feed_tts():
        """Collect LLM tokens and send to TTS"""
        text_buffer = ""
        async for token in llm_stream:
            text_buffer += token
            
            # Send to TTS every 40 chars or at punctuation
            if any(text_buffer.endswith(p) for p in '.!?'):
                await tts_queue.put(text_buffer.strip())
                text_buffer = ""
            elif len(text_buffer) > 40:
                await tts_queue.put(text_buffer)
                text_buffer = ""
        
        if text_buffer:
            await tts_queue.put(text_buffer)
    
    async def stream_audio():
        """Stream TTS audio chunks as they arrive"""
        while True:
            try:
                text_chunk = tts_queue.get_nowait()
                async for audio_chunk in self.tts_router.synthesize(text_chunk):
                    yield audio_chunk
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.05)
    
    # Run both tasks in parallel
    await asyncio.gather(feed_tts(), stream_audio())
```

- [ ] Token streaming from LLM
- [ ] Queue-based buffering (maxsize=10)
- [ ] Parallel LLM + TTS
- [ ] Tests for latency

**Effort**: 36 hours

---

### ✅ Phase 2 Summary

| Спринт | Компоненты | Time | Owner |
|--------|-----------|------|-------|
| 2.1 | Call Management | 108h | Backend (Node.js) |
| 2.2 | LLM/TTS/STT | 136h | Backend (Python) |
| **TOTAL** | | **244h** | 3 people |

**Milestone**: Могу создать агента, настроить голос, и при тестовом звонке LLM отвечает с голосом.

---

## 💳 PHASE 3: BILLING & SIP INTEGRATION (Weeks 7-10)

### Sprint 3.1: Billing System (Week 7-8)

#### Database Schema:

```sql
CREATE TABLE balances (
    org_id UUID PRIMARY KEY,
    balance_kopecks NUMERIC(10, 2),
    last_event_id BIGINT,
    updated_at TIMESTAMP
);

CREATE TABLE billing_events (
    id BIGSERIAL PRIMARY KEY,
    org_id UUID,
    event_type VARCHAR(50),
    amount_kopecks NUMERIC(10, 2),
    idempotency_key VARCHAR(255) UNIQUE,
    call_id UUID,
    yookassa_payment_id VARCHAR(255),
    created_at TIMESTAMP
);

CREATE INDEX billing_events_org_id ON billing_events(org_id);
CREATE INDEX billing_events_idempotency ON billing_events(idempotency_key);
```

**Задачи:**

**3.1.1 Call Cost Calculation & Deduction**

```typescript
interface BillingConfig {
  perMinuteRate: number;  // kopecks per minute
  minBillingUnit: number; // 1 minute minimum
}

async function endCall(callId: string) {
  const call = await getCall(callId);
  const durationMinutes = Math.ceil(call.durationSeconds / 60);
  const cost = durationMinutes * config.perMinuteRate;
  
  // Deduct with idempotency
  await deductBalance(
    call.org_id,
    cost,
    `call_ended:${callId}`  // idempotency_key
  );
}

async function deductBalance(
  org_id: string,
  amount: number,
  idempotencyKey: string
) {
  // 1. Check if already applied
  const existing = await db.query(
    `SELECT id FROM billing_events 
     WHERE org_id = $1 AND idempotency_key = $2`,
    org_id, idempotencyKey
  );
  
  if (existing) {
    logger.info(`Event ${idempotencyKey} already applied`);
    return;
  }
  
  // 2. Insert event (UNIQUE constraint prevents duplicates)
  await db.query(
    `INSERT INTO billing_events 
     (org_id, event_type, amount_kopecks, idempotency_key)
     VALUES ($1, 'call_ended', $2, $3)`,
    org_id, amount, idempotencyKey
  );
  
  // 3. Recalculate balance from all events
  const newBalance = await db.query_scalar(
    `SELECT COALESCE(SUM(CASE 
        WHEN event_type = 'payment_received' THEN amount_kopecks
        WHEN event_type = 'call_ended' THEN -amount_kopecks
        ELSE 0
      END), 0)
     FROM billing_events WHERE org_id = $1`,
    org_id
  );
  
  // 4. Update denormalized balance table
  await db.query(
    `UPDATE balances 
     SET balance_kopecks = $1, updated_at = NOW()
     WHERE org_id = $2`,
    newBalance, org_id
  );
  
  // 5. Publish event
  await kafka.publish('billing-events', {
    org_id,
    event_type: 'call_ended',
    amount_kopecks: amount,
    new_balance: newBalance,
    timestamp: new Date()
  });
}
```

- [ ] Cost calculation logic
- [ ] Idempotent deduction
- [ ] Balance updates
- [ ] Event sourcing pattern
- [ ] Tests (especially idempotency)

**Effort**: 40 hours

---

**3.1.2 YooKassa Payment Integration**

```typescript
interface CreatePaymentRequest {
  amount: number;           // kopecks
  description: string;
  returnUrl: string;
}

async function createPayment(org_id: string, amount: number) {
  const payment = await yookassa.createPayment({
    amount: { value: (amount / 100).toFixed(2), currency: 'RUB' },
    confirmation: {
      type: 'redirect',
      return_url: `${APP_URL}/billing/success`
    },
    description: `Balance replenishment for ${org_id}`,
    metadata: { org_id }
  });
  
  return {
    paymentId: payment.id,
    confirmationUrl: payment.confirmation.confirmation_url
  };
}
```

- [ ] YooKassa SDK integration
- [ ] Create payment endpoint (POST /billing/payments)
- [ ] Get payment status endpoint
- [ ] Redirect to payment form

**Effort**: 28 hours

---

**3.1.3 Webhook Processing (Idempotent!)**

```typescript
// POST /billing/webhooks/yookassa
async function handleYooKassaWebhook(event: YooKassaEvent) {
  if (event.type !== 'payment.succeeded') return;
  
  const payment = event.object;
  const orgId = payment.metadata.org_id;
  const amount = Math.round(parseFloat(payment.amount.value) * 100); // to kopecks
  
  // Use idempotency key to ensure exactly-once processing
  const idempotencyKey = `payment:${payment.id}`;
  
  await addBalance(orgId, amount, idempotencyKey);
}

async function addBalance(
  org_id: string,
  amount: number,
  idempotencyKey: string
) {
  // 1. Check if already processed
  const existing = await db.query(
    `SELECT id FROM billing_events 
     WHERE org_id = $1 AND idempotency_key = $2`,
    org_id, idempotencyKey
  );
  
  if (existing) {
    logger.info(`Payment ${idempotencyKey} already processed`);
    return;
  }
  
  // 2. Insert event
  await db.query(
    `INSERT INTO billing_events 
     (org_id, event_type, amount_kopecks, idempotency_key)
     VALUES ($1, 'payment_received', $2, $3)`,
    org_id, amount, idempotencyKey
  );
  
  // 3-5. Same as deductBalance...
  const newBalance = await calculateBalance(org_id);
  await updateBalance(org_id, newBalance);
  
  await kafka.publish('billing-events', {
    type: 'payment_received',
    org_id,
    amount_kopecks: amount,
    new_balance: newBalance
  });
}
```

- [ ] Webhook signature verification (YooKassa signs webhooks)
- [ ] Idempotent processing
- [ ] Retry logic if processing fails
- [ ] Notification emails
- [ ] Tests

**Effort**: 32 hours

---

**3.1.4 Balance Check Before Call**

```typescript
async function canInitiateCall(org_id: string): Promise<boolean> {
  const balance = await getBalance(org_id);
  const estimatedCost = 60; // 1 minute minimum
  
  if (balance < estimatedCost) {
    logger.warn(`Insufficient balance for org ${org_id}`);
    await kafka.publish('billing-events', {
      type: 'call_rejected',
      org_id,
      reason: 'insufficient_balance'
    });
    return false;
  }
  
  return true;
}

// In Call Service
async function initiateCall(params: InitiateCallParams) {
  if (!await canInitiateCall(params.organizationId)) {
    throw new BillingError('Insufficient balance');
  }
  
  // Proceed with call
}
```

- [ ] Balance check before accepting call
- [ ] Reject call if insufficient funds
- [ ] Publish event for monitoring

**Effort**: 16 hours

---

### Sprint 3.2: SIP Integration (Week 9-10)

#### Задачи:

**3.2.1 MTS Exolve SIP Setup**

```typescript
// Using PJSUA2 (SIP library)
import pjsua2 from 'pjsua2';

class SIPManager {
  private sipEndpoint: pjsua2.Endpoint;
  
  async initialize() {
    // Create endpoint
    this.sipEndpoint = new pjsua2.Endpoint();
    
    // Register with MTS Exolve
    const account = new pjsua2.Account();
    account.create({
      idUri: "sip:your_sip_user@exolve.mts.ru",
      regConfig: new pjsua2.AccountRegConfig({
        registrarUri: "sip:exolve.mts.ru",
        authScheme: "digest",
        authCred: [new pjsua2.AuthCred({
          realm: "mts.ru",
          username: "your_username",
          password: "your_password",
          scheme: "digest"
        })]
      })
    });
    
    await this.monitorRegistration(account);
  }
  
  private async monitorRegistration(account: pjsua2.Account) {
    // Monitor registration status
    setInterval(() => {
      const info = account.getInfo();
      logger.info(`SIP registration status: ${info.regStatus}`);
      
      if (info.regStatus !== 200) {
        this.handleRegistrationFailure(account);
      }
    }, 30000);
  }
}
```

- [ ] PJSUA2 setup
- [ ] MTS Exolve credentials configuration
- [ ] Registration monitoring
- [ ] Error handling

**Effort**: 20 hours

---

**3.2.2 Incoming Call Handling**

```typescript
async function handleIncomingCall(
  event: pjsua2.OnIncomingCallParam
) {
  const call = event.call;
  const callInfo = call.getInfo();
  
  logger.info(`📞 Incoming call from ${callInfo.remoteUri}`);
  
  // Extract phone number
  const fromNumber = extractPhoneNumber(callInfo.remoteUri);
  const toNumber = extractPhoneNumber(callInfo.localUri);
  
  // Find agent for this phone number
  const phoneNumber = await db.query(
    `SELECT agent_id, org_id FROM phone_numbers 
     WHERE number = $1 AND status = 'active'`,
    toNumber
  );
  
  if (!phoneNumber) {
    call.hangup(404);
    logger.warn(`No agent configured for ${toNumber}`);
    return;
  }
  
  // Check balance
  if (!await canInitiateCall(phoneNumber.org_id)) {
    call.hangup(480);  // Temporarily Unavailable
    return;
  }
  
  // Create call record
  const callRecord = await createCall({
    org_id: phoneNumber.org_id,
    agent_id: phoneNumber.agent_id,
    from_number: fromNumber,
    to_number: toNumber,
    direction: 'inbound'
  });
  
  // Accept call
  call.answer(200);
  
  // Publish event
  await kafka.publish('call-events', {
    type: 'call.initiated',
    call_id: callRecord.id,
    org_id: phoneNumber.org_id,
    agent_id: phoneNumber.agent_id,
    from_number: fromNumber,
    to_number: toNumber,
    direction: 'inbound'
  });
}
```

- [ ] Call routing to correct agent
- [ ] Call record creation
- [ ] Balance check
- [ ] Accept/reject logic

**Effort**: 28 hours

---

**3.2.3 SIP Circuit Breaker**

```typescript
class SIPCircuitBreaker {
  private failures = 0;
  private successes = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';
  private lastStateChange = Date.now();
  
  private readonly FAILURE_THRESHOLD = 5;
  private readonly SUCCESS_THRESHOLD = 3;
  private readonly TIMEOUT = 30000;  // 30 seconds
  
  record_success() {
    if (this.state === 'half-open') {
      this.successes++;
      if (this.successes >= this.SUCCESS_THRESHOLD) {
        logger.info("🟢 Circuit breaker CLOSED");
        this.state = 'closed';
        this.failures = 0;
        this.successes = 0;
      }
    } else {
      this.failures = 0;
    }
  }
  
  record_failure() {
    this.failures++;
    
    if (this.failures >= this.FAILURE_THRESHOLD) {
      logger.error("🔴 Circuit breaker OPEN - SIP service unavailable");
      this.state = 'open';
      this.lastStateChange = Date.now();
    }
  }
  
  is_open(): boolean {
    if (this.state === 'open') {
      const elapsed = Date.now() - this.lastStateChange;
      if (elapsed > this.TIMEOUT) {
        logger.info("🟡 Circuit breaker HALF-OPEN - testing recovery");
        this.state = 'half-open';
        this.successes = 0;
        return false;
      }
      return true;
    }
    return false;
  }
}

// Usage:
const sipCircuitBreaker = new SIPCircuitBreaker();

async function handleIncomingCall(event) {
  if (sipCircuitBreaker.is_open()) {
    event.call.hangup(503);  // Service Unavailable
    return;
  }
  
  try {
    await processCall(event);
    sipCircuitBreaker.record_success();
  } catch (e) {
    sipCircuitBreaker.record_failure();
    throw e;
  }
}
```

- [ ] Circuit breaker implementation
- [ ] State transitions (closed → open → half-open)
- [ ] Automatic recovery testing

**Effort**: 24 hours

---

### ✅ Phase 3 Summary

| Спринт | Компоненты | Time | Owner |
|--------|-----------|------|-------|
| 3.1 | Billing System | 116h | Backend |
| 3.2 | SIP Integration | 72h | Backend |
| **TOTAL** | | **188h** | 2-3 people |

**Milestone**: Могу создать платеж, пополнить баланс, принять входящий SIP звонок.

---

## 🎨 PHASE 4: FRONTEND & MONITORING (Weeks 11-13)

### Sprint 4.1: Dashboard Frontend (Week 11-12)

#### Tech Stack:
- Next.js 15 + React 19
- TypeScript
- Tailwind CSS
- SWR для data fetching
- Chart.js для графиков

**4.1.1 Admin Dashboard**

```tsx
// pages/dashboard/index.tsx
import { DashboardLayout } from '@/components/layout';
import { CallsChart } from '@/components/charts';
import { ActiveCalls } from '@/components/calls';
import { BalanceCard } from '@/components/billing';

export default function Dashboard() {
  const { data: stats } = useFetch('/api/stats');
  const { data: activeCalls } = useFetch('/api/calls/active');
  const { data: balance } = useFetch('/api/billing/balance');
  
  return (
    <DashboardLayout>
      <div className="grid grid-cols-4 gap-4">
        <BalanceCard balance={balance} />
        <StatsCard label="Active Calls" value={stats.activeCalls} />
        <StatsCard label="Total Agents" value={stats.totalAgents} />
        <StatsCard label="Today's Revenue" value={stats.todayRevenue} />
      </div>
      
      <div className="mt-8 grid grid-cols-2 gap-8">
        <CallsChart data={stats.callsByHour} />
        <ActiveCalls calls={activeCalls} />
      </div>
    </DashboardLayout>
  );
}
```

- [ ] Dashboard layout
- [ ] Key metrics display
- [ ] Real-time updates (WebSocket)
- [ ] Responsive design

**Effort**: 40 hours

---

**4.1.2 Agent Management UI**

```tsx
// pages/agents/index.tsx
import { AgentForm } from '@/components/agents';
import { AgentList } from '@/components/agents';

export default function AgentsPage() {
  const [isCreating, setIsCreating] = useState(false);
  const { data: agents, mutate } = useFetch('/api/agents');
  
  return (
    <div>
      <h1>Agents</h1>
      <button onClick={() => setIsCreating(true)}>
        Create Agent
      </button>
      
      {isCreating && (
        <AgentForm
          onSubmit={async (data) => {
            await fetch('/api/agents', {
              method: 'POST',
              body: JSON.stringify(data)
            });
            mutate();
            setIsCreating(false);
          }}
        />
      )}
      
      <AgentList agents={agents} />
    </div>
  );
}
```

- [ ] Create agent form
- [ ] Edit agent form
- [ ] List view with filters
- [ ] Delete with confirmation
- [ ] Tests

**Effort**: 32 hours

---

**4.1.3 Billing UI**

```tsx
// pages/billing/index.tsx
import { BalanceCard } from '@/components/billing';
import { PaymentHistory } from '@/components/billing';
import { PaymentForm } from '@/components/billing';

export default function BillingPage() {
  const { data: balance } = useFetch('/api/billing/balance');
  const { data: transactions } = useFetch('/api/billing/transactions');
  
  return (
    <div>
      <BalanceCard balance={balance} />
      
      <PaymentForm
        onPayment={async (amount) => {
          const response = await fetch('/api/billing/payments', {
            method: 'POST',
            body: JSON.stringify({ amount })
          });
          window.location.href = response.confirmationUrl;
        }}
      />
      
      <PaymentHistory transactions={transactions} />
    </div>
  );
}
```

- [ ] Balance display
- [ ] Payment form
- [ ] Transaction history
- [ ] Download invoices

**Effort**: 28 hours

---

**4.1.4 Call Monitor (Real-time)**

```tsx
// pages/calls/[id].tsx
import { LiveTranscript } from '@/components/calls';
import { CallStats } from '@/components/calls';

export default function CallMonitorPage({ callId }: { callId: string }) {
  const [transcript, setTranscript] = useState<Message[]>([]);
  const [callStats, setCallStats] = useState(null);
  
  useEffect(() => {
    // WebSocket connection
    const ws = new WebSocket(`wss://api.app/ws/calls/${callId}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'message') {
        setTranscript(prev => [...prev, data.message]);
      }
      
      if (data.type === 'stats_update') {
        setCallStats(data.stats);
      }
    };
    
    return () => ws.close();
  }, [callId]);
  
  return (
    <div className="flex gap-8">
      <LiveTranscript messages={transcript} />
      <CallStats stats={callStats} />
    </div>
  );
}
```

- [ ] WebSocket connection
- [ ] Live transcript display
- [ ] Real-time stats
- [ ] Audio player

**Effort**: 36 hours

---

### Sprint 4.2: Monitoring & Observability (Week 13)

**4.2.1 Prometheus Metrics**

```python
# In all services
from prometheus_client import Counter, Histogram, Gauge

# Metrics
call_duration = Histogram(
    'call_duration_seconds',
    'Duration of calls',
    buckets=(1, 10, 30, 60, 300, 600)
)

call_errors = Counter(
    'call_errors_total',
    'Total number of call errors',
    ['reason']
)

concurrent_calls = Gauge(
    'concurrent_calls_active',
    'Number of active calls'
)

llm_latency = Histogram(
    'llm_inference_ms',
    'LLM inference latency',
    buckets=(100, 200, 500, 1000, 2000, 5000)
)

billing_transactions = Counter(
    'billing_transactions_total',
    'Total billing transactions',
    ['type']
)

# Usage:
@app.post("/calls")
async def create_call(params):
  with call_duration.time():
    call = await call_service.create(params)
  return call
```

- [ ] Metrics in all services
- [ ] Prometheus scrape configuration
- [ ] Grafana dashboard setup

**Effort**: 32 hours

---

**4.2.2 Structured Logging & Tracing**

```typescript
import pino from 'pino';
import { trace } from '@opentelemetry/api';

const logger = pino({
  transport: {
    target: 'pino-loki',  // Send to Loki
    options: {
      host: 'localhost',
      port: 3100
    }
  }
});

const tracer = trace.getTracer('voice-agent');

@app.post("/calls")
async function createCall(req, res) {
  const span = tracer.startSpan('create_call');
  
  logger.info({
    trace_id: span.spanContext().traceId,
    call_id: call.id,
    org_id: req.org.id,
    action: 'call_initiated'
  });
  
  span.end();
}
```

- [ ] Pino logger setup
- [ ] OpenTelemetry tracing
- [ ] Loki log aggregation
- [ ] Jaeger distributed tracing

**Effort**: 28 hours

---

**4.2.3 Alerting Rules**

```yaml
# prometheus_rules.yml
groups:
  - name: voice-agent
    rules:
      - alert: HighErrorRate
        expr: rate(call_errors_total[5m]) > 0.01
        annotations:
          summary: "High call error rate"
      
      - alert: SlowLLMInference
        expr: llm_inference_ms{quantile="0.99"} > 1000
        annotations:
          summary: "LLM inference is slow"
      
      - alert: BillingWebhookLatency
        expr: billing_webhook_latency_ms{quantile="0.95"} > 5000
        annotations:
          summary: "Billing webhook is slow"
      
      - alert: KafkaLagHigh
        expr: kafka_consumer_lag > 60000
        annotations:
          summary: "Kafka consumer lag is high"
```

- [ ] Alert rules configuration
- [ ] AlertManager setup
- [ ] Slack/Email notifications

**Effort**: 16 hours

---

### ✅ Phase 4 Summary

| Компонент | Time | Owner |
|-----------|------|-------|
| Frontend Dashboard | 136h | Frontend |
| Monitoring/Tracing | 76h | DevOps/Backend |
| **TOTAL** | **212h** | 3 people |

**Milestone**: Dashboard работает, видно live calls, метрики отправляются в Prometheus.

---

## 🔐 PHASE 5: SECURITY & HARDENING (Weeks 14-16)

### Sprint 5.1: Security Hardening (Week 14-15)

**5.1.1 PII Masking in Logs**

```typescript
// utils/logger.ts
function maskPII(obj: any): any {
  if (typeof obj !== 'object') return obj;
  
  return Object.fromEntries(
    Object.entries(obj).map(([key, value]) => {
      if (key.toLowerCase().includes('phone') && typeof value === 'string') {
        return [key, value.slice(0, 4) + '*'.repeat(5) + value.slice(-4)];
      }
      if (key.toLowerCase().includes('email') && typeof value === 'string') {
        const [name, domain] = value.split('@');
        return [key, name.slice(0, 2) + '*'.repeat(3) + '@' + domain];
      }
      return [key, value];
    })
  );
}

// Usage:
logger.info(maskPII({
  phone: '+7912345678',
  email: 'user@example.com'
}));
// Output: { phone: '+791****5678', email: 'us***@example.com' }
```

- [ ] PII masking utility
- [ ] Apply to all loggers
- [ ] Tests

**Effort**: 12 hours

---

**5.1.2 API Key Security**

```typescript
import crypto from 'crypto';

// When creating API key
const plainKey = crypto.randomBytes(32).toString('hex');
const hash = crypto
  .createHash('sha256')
  .update(plainKey)
  .update(salt)
  .digest('hex');

await db.query(
  `INSERT INTO api_keys (key_hash, ...) VALUES ($1, ...)`,
  hash
);

return plainKey;  // Only shown once to user!

// When validating API key
const providedKey = req.headers['x-api-key'];
const hash = crypto
  .createHash('sha256')
  .update(providedKey)
  .update(salt)
  .digest('hex');

const key = await db.query(
  `SELECT * FROM api_keys WHERE key_hash = $1`,
  hash
);
```

- [ ] Generate with crypto.randomBytes
- [ ] Hash with SHA-256 + salt before storing
- [ ] Never log full keys
- [ ] Rotation policy (1 year lifetime)
- [ ] Alert on suspicious usage

**Effort**: 20 hours

---

**5.1.3 Rate Limiting & DDoS Protection**

```typescript
// redis-backed distributed rate limiting
import { RateLimiter } from 'rate-limiter-flexible';

const limiter = new RateLimiter({
  points: 200,      // 200 requests
  duration: 60,     // per 60 seconds
  blockDuration: 0, // no block, just reject
});

app.use(async (req, res, next) => {
  const key = `${req.userId}:${req.ip}`;
  
  try {
    await limiter.consume(key);
    next();
  } catch (err) {
    res.status(429).json({ error: 'Too many requests' });
  }
});
```

- [ ] Redis-backed rate limiter
- [ ] Per-user and per-IP limits
- [ ] CloudFlare DDoS protection
- [ ] WAF rules

**Effort**: 24 hours

---

**5.1.4 GDPR Compliance**

```typescript
// POST /organizations/:id/export-data
async function exportData(orgId: string) {
  // Collect all user data
  const users = await db.query(
    `SELECT * FROM users WHERE org_id = $1`,
    orgId
  );
  
  const calls = await db.query(
    `SELECT * FROM calls WHERE org_id = $1`,
    orgId
  );
  
  const conversations = await db.query(
    `SELECT * FROM conversations 
     WHERE call_id IN (SELECT id FROM calls WHERE org_id = $1)`,
    orgId
  );
  
  // Create ZIP with all data
  return createZip({
    users,
    calls,
    conversations,
    billing_events: await getBillingEvents(orgId)
  });
}

// DELETE /organizations/:id/all-data
async function deleteAllData(orgId: string) {
  // Requires verification (email confirmation)
  
  // Delete in order of foreign keys
  await db.query(`DELETE FROM conversations WHERE org_id = $1`, orgId);
  await db.query(`DELETE FROM calls WHERE org_id = $1`, orgId);
  await db.query(`DELETE FROM agent_tools WHERE agent_id IN 
    (SELECT id FROM agents WHERE org_id = $1)`, orgId);
  await db.query(`DELETE FROM agents WHERE org_id = $1`, orgId);
  await db.query(`DELETE FROM users WHERE org_id = $1`, orgId);
  await db.query(`DELETE FROM organizations WHERE id = $1`, orgId);
}
```

- [ ] Data export endpoint
- [ ] Right to delete implementation
- [ ] Data retention policy
- [ ] Privacy policy page

**Effort**: 28 hours

---

**5.1.5 Encryption & Secrets Management**

```bash
# Use AWS Secrets Manager
aws secretsmanager create-secret --name voice-agent/openai-api-key \
  --secret-string "sk-..."

aws secretsmanager create-secret --name voice-agent/yookassa-secret \
  --secret-string "..."

aws secretsmanager rotate-secret --secret-id voice-agent/openai-api-key \
  --rotation-rules AutomaticallyAfterDays=90
```

- [ ] AWS Secrets Manager setup
- [ ] Secret rotation configuration
- [ ] Remove .env files from production
- [ ] Audit logging for secret access

**Effort**: 16 hours

---

### Sprint 5.2: Testing & Deployment (Week 16)

**5.2.1 Load Testing**

```yaml
# k6 load test script
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: 100,           // 100 virtual users
  duration: '1m',     // for 1 minute
};

export default function () {
  // Test login
  let response = http.post(`${BASE_URL}/auth/login`, {
    email: 'test@example.com',
    password: 'password'
  });
  
  check(response, {
    'login successful': (r) => r.status === 200,
  });
  
  const token = response.json('token');
  
  // Test create agent
  response = http.post(
    `${BASE_URL}/agents`,
    {
      name: `Agent ${__VU}`,
      system_prompt: 'You are helpful',
      llm_model: 'gpt-4o-mini'
    },
    {
      headers: { Authorization: `Bearer ${token}` }
    }
  );
  
  check(response, {
    'create agent successful': (r) => r.status === 201,
  });
  
  sleep(1);
}
```

- [ ] k6 load testing script
- [ ] Simulate 100-1000 concurrent users
- [ ] Identify bottlenecks
- [ ] Document results

**Effort**: 24 hours

---

**5.2.2 Canary Deployment**

```yaml
# GitOps: FluxCD/ArgoCD setup
apiVersion: apps/v1
kind: Deployment
metadata:
  name: voice-agent-api
spec:
  replicas: 3
  strategy:
    type: Canary
    canary:
      steps:
        - setWeight: 10    # 10% traffic to new version
        - pause: { duration: 10m }
        - setWeight: 50    # 50% traffic
        - pause: { duration: 10m }
        - setWeight: 100   # 100% traffic
```

- [ ] Canary deployment setup
- [ ] Automated rollback on errors
- [ ] Feature flags for gradual rollout

**Effort**: 20 hours

---

**5.2.3 Disaster Recovery Testing**

```bash
# Monthly DR test
1. Stop primary database
2. Failover to replica
3. Verify all features work
4. Measure RTO (Recovery Time Objective) and RPO

# Runbook for incidents
1. Database down → Failover to read replica
2. Kafka unavailable → Queue in Redis, retry later
3. LLM service down → Use fallback (Claude or Llama)
4. Payment service down → Reject calls, notify ops
5. Full outage → Notify customers, post on status page
```

- [ ] Backup restoration test
- [ ] Failover procedures
- [ ] Runbook documentation
- [ ] Monthly DR drills

**Effort**: 20 hours

---

### ✅ Phase 5 Summary

| Компонент | Time | Owner |
|-----------|------|-------|
| Security Hardening | 100h | Backend |
| Testing & Deployment | 64h | QA/DevOps |
| **TOTAL** | **164h** | 2-3 people |

**Milestone**: Production-ready, secure, auditable, tested with load.

---

## 📊 IMPLEMENTATION TIMELINE

```
TOTAL PROJECT: 16 weeks (4 months)

Week  1-2:   Foundation (Auth, DB, API Gateway)        172h
Week  3-6:   Core Calls (LLM, TTS, STT)                244h
Week  7-10:  Billing & SIP                             188h
Week  11-13: Frontend & Monitoring                     212h
Week  14-16: Security & Hardening                      164h
             ─────────────────────────────────────────────
             TOTAL:                                    980h

Team composition (recommended):
  - 1 Tech Lead (full time)
  - 2 Backend Engineers (full time)
  - 1 Frontend Engineer (full time)
  - 1 DevOps Engineer (part-time, 50%)
  ─────────────────────────────────
  Total: 4.5 FTE

Cost estimate (avg $100/hour):
  980h × $100 = $98,000 (base development)
  + Infrastructure: ~$5,000-10,000
  + Tools & services: ~$3,000-5,000
  ─────────────────
  Total: ~$110,000-115,000

Timeline by team size:
  - 4.5 FTE:  16 weeks
  - 3 FTE:    24 weeks
  - 2 FTE:    40 weeks
```

---

## 🎯 SPRINT STRUCTURE & CEREMONIES

### Weekly Sprint (Monday-Friday)

```
Monday 10:00 - Sprint Planning
├─ Pick issues from backlog
├─ Estimate story points
└─ Assign to engineers

Daily 10:30 - Standup (15 min)
├─ What I did yesterday
├─ What I'm doing today
└─ Blockers?

Wednesday 15:00 - Technical Sync
├─ Architecture discussions
├─ Cross-service integration
└─ Dependency resolution

Friday 16:00 - Sprint Review
├─ Demo what we built
└─ Stakeholder feedback

Friday 16:45 - Retrospective
├─ What went well?
├─ What to improve?
└─ Action items for next sprint
```

---

## 📝 DEFINITION OF DONE (DoD)

Every feature/bug must meet these criteria before marking "Done":

- [ ] Code written (TypeScript/Python with proper types)
- [ ] Code reviewed by 1+ engineer
- [ ] Unit tests (>80% coverage)
- [ ] Integration tests pass
- [ ] Documented (comments, README updates)
- [ ] No console.error or warnings in logs
- [ ] Works on staging environment
- [ ] Performance baseline met (P99 < SLA)
- [ ] Security review completed (if applicable)
- [ ] Product Owner approved

---

## 🚀 DEPLOYMENT CHECKLIST

Before each release to production:

- [ ] All tests passing (unit + integration)
- [ ] Load testing completed (k6 with 100+ vus)
- [ ] Security audit completed
- [ ] Database migrations tested
- [ ] Rollback procedure documented
- [ ] Monitoring alerts configured
- [ ] On-call runbook updated
- [ ] Stakeholders notified
- [ ] Canary deployment (10% → 50% → 100%)
- [ ] Post-deploy smoke tests

---

## 📞 SUPPORT STRUCTURES

### Escalation Path
```
Developer
    ↓
Tech Lead
    ↓
Engineering Manager
    ↓
CTO
```

### Communication Channels
- **Slack #voice-agent-dev** - daily updates
- **Slack #voice-agent-incidents** - critical issues
- **Weekly syncs** - Thu 10:00 (30 min)
- **Monthly stakeholder** - board view of progress

---

## 🏁 SUCCESS METRICS

By end of Phase 5:

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| API availability | 99.9% | - | 🟡 To measure |
| P99 latency | <300ms | - | 🟡 To measure |
| Call error rate | <0.5% | - | 🟡 To measure |
| Frontend load time | <2s | - | 🟡 To measure |
| Test coverage | >80% | - | 🟡 To measure |
| Security score | A+ | - | 🟡 To audit |
| Production incidents | <1/month | - | 🟡 To track |

---

## 📖 ADDITIONAL RESOURCES

### Documentation to Create

1. **Architecture Decision Records (ADRs)**
   - Why we chose Node.js for API
   - Why Kafka for events
   - Why Python for Agent Orchestration

2. **API Documentation**
   - OpenAPI 3.0 spec
   - Postman collection
   - Example requests/responses

3. **Deployment Guide**
   - How to deploy to production
   - Rollback procedures
   - Emergency contacts

4. **Runbook**
   - Common issues and solutions
   - Escalation procedures
   - On-call responsibilities

5. **Architecture Diagrams**
   - C4 model diagrams
   - Sequence diagrams for key flows
   - Data flow diagrams

---

## 🎓 TEAM ONBOARDING

New engineers should:

1. **Week 1**: Setup, environment, architecture overview
2. **Week 2**: Pick small task (DB migration, simple endpoint)
3. **Week 3**: Medium task (new API endpoint with tests)
4. **Week 4**: Complex task (with mentoring)

Resources:
- [ ] README with setup instructions
- [ ] Architecture documentation
- [ ] Code examples for patterns
- [ ] Pair programming sessions
- [ ] Code walkthroughs

---

**Document Version**: 1.0  
**Last Updated**: December 2025  
**Next Review**: January 2026  

---

## CONCLUSION

Этот документ дает четкий план на **16 недель разработки** с:

✅ Разбивкой на 5 фаз  
✅ Конкретными задачами для каждого спринта  
✅ Оценками времени (980 часов)  
✅ Рекомендуемым составом команды (4.5 FTE)  
✅ Definition of Done и процессами  

Каждый инженер может взять issue, посмотреть в этот документ, и понять:
- Что нужно сделать
- Почему это нужно
- На что это влияет
- Примеры кода
- Effort и timeline

👍 **Ready to build!**
