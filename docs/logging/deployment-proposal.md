# Proposed app-deployment changes (not applied)

Generated 14 September 2026 from `bfi-finance/app-deployment` at `master`. Each block is a unified diff against the file as it is today. Nothing here has been committed or pushed; these are for SRE and the owning squad to apply, trim, or reject.

## 1. Production log level debug -> info

### `audit-trail/values-prod.yaml`

- LOGGER_LEVEL: 'debug' -> 'info'

```diff
--- a/audit-trail/values-prod.yaml
+++ b/audit-trail/values-prod.yaml
@@ -119,5 +119,5 @@
       value: "true"
     - name: LOGGER_LEVEL
-      value: "debug"
+      value: "info"
     - name: LOGGER_OUTPUT
       value: "stdout"
```

### `gen-ai/values-prod.yaml`

- LOGGER_LEVEL: 'debug' -> 'info'

```diff
--- a/gen-ai/values-prod.yaml
+++ b/gen-ai/values-prod.yaml
@@ -105,5 +105,5 @@
       value: "true"
     - name: LOGGER_LEVEL
-      value: "debug"
+      value: "info"
     - name: LOGGER_OUTPUT
       value: "stdout"
```

### `partnership-provisioning/values-prod.yaml`

- LOGGER_LEVEL: 'debug' -> 'info'

```diff
--- a/partnership-provisioning/values-prod.yaml
+++ b/partnership-provisioning/values-prod.yaml
@@ -85,5 +85,5 @@
       value: "true"
     - name: LOGGER_LEVEL
-      value: "debug"
+      value: "info"
     - name: LOGGER_OUTPUT
       value: "stdout"
```

### `robot-controller/values-prod.yaml`

- LOGGER_LEVEL: 'debug' -> 'info'

```diff
--- a/robot-controller/values-prod.yaml
+++ b/robot-controller/values-prod.yaml
@@ -109,5 +109,5 @@
       value: "true"
     - name: LOGGER_LEVEL
-      value: "debug"
+      value: "info"
     - name: LOGGER_OUTPUT
       value: "stdout"
```

### `supplier/values-prod.yaml`

- LOGGER_LEVEL: 'debug' -> 'info'

```diff
--- a/supplier/values-prod.yaml
+++ b/supplier/values-prod.yaml
@@ -91,5 +91,5 @@
       value: "true"
     - name: LOGGER_LEVEL
-      value: "debug"
+      value: "info"
     - name: LOGGER_OUTPUT
       value: "stdout"
```

### `doc-renderer/values-prod.yaml`

- LOGGER_LEVEL: 'debug' -> 'info'

```diff
--- a/doc-renderer/values-prod.yaml
+++ b/doc-renderer/values-prod.yaml
@@ -103,5 +103,5 @@
       value: "true"
     - name: LOGGER_LEVEL
-      value: "debug"
+      value: "info"
     - name: LOGGER_OUTPUT
       value: "stdout"
```

### `gold-service/values-prod.yaml`

- LOGGER_LEVEL: 'debug' -> 'info'
- POSTGRES_LOG_LEVEL: 'debug' -> 'info'

```diff
--- a/gold-service/values-prod.yaml
+++ b/gold-service/values-prod.yaml
@@ -76,5 +76,5 @@
       value: "TRUE"
     - name: LOGGER_LEVEL
-      value: "debug"
+      value: "info"
     - name: LOGGER_OUTPUT
       value: "stdout"
@@ -170,5 +170,5 @@
       value: "TRUE"
     - name: POSTGRES_LOG_LEVEL
-      value: "debug"
+      value: "info"
     - name: POSTGRES_CONN_MAX_OPEN
       value: "10"
```

### `portfolio-management-service/values-prod.yaml`

- LOGGER_LEVEL: 'debug' -> 'info'
- POSTGRES_LOG_LEVEL: 'debug' -> 'info'

```diff
--- a/portfolio-management-service/values-prod.yaml
+++ b/portfolio-management-service/values-prod.yaml
@@ -80,5 +80,5 @@
       value: "true"
     - name: LOGGER_LEVEL
-      value: "debug"
+      value: "info"
     - name: LOGGER_OUTPUT
       value: "stdout"
@@ -170,5 +170,5 @@
       value: "10"
     - name: POSTGRES_LOG_LEVEL
-      value: "debug"
+      value: "info"
     - name: POSTGRES_HOST
       value: "127.0.0.1"
```

### `robot-scrape/values-prod.yaml`

- LOG_LEVEL: 'DEBUG' -> 'INFO'

```diff
--- a/robot-scrape/values-prod.yaml
+++ b/robot-scrape/values-prod.yaml
@@ -66,5 +66,5 @@
       value: "8080"
     - name: LOG_LEVEL
-      value: "DEBUG"
+      value: "INFO"
     - name: DMS_API_URL
       value: "http://prod-ms-document.prod.svc.cluster.local"
```

## 2. A masked-field list where bodies are logged and the list is empty

### `lora-gateway/values-prod.yaml`

- HTTP_SERVER_REQUEST_BODY_JSON_MASKED_FIELDS: '' -> 'access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_…
- HTTP_SERVER_RESPONSE_BODY_JSON_MASKED_FIELDS: '' -> 'access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity…
- HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS: '' -> 'access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_…
- HTTP_CLIENT_RESPONSE_BODY_JSON_MASKED_FIELDS: '' -> 'access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity…

```diff
--- a/lora-gateway/values-prod.yaml
+++ b/lora-gateway/values-prod.yaml
@@ -121,5 +121,5 @@
       value: "32768"
     - name: HTTP_SERVER_REQUEST_BODY_JSON_MASKED_FIELDS
-      value: ""
+      value: "access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_photo_id,idNumber,ktp,ktp_data,ktp_doc_id,ktp_number,mother_maiden_name,mother_name,new_password,new_password_confirmation,nik,npwp_number,old_password,otp,otp_token,password,placeOfBirth,pob,refresh_token,selfie,selfie_doc_id,selfie_photo_id,signature,token,religion,legal_address,birth_place,city_code,city_name,district_code,district_name,province_code,province_name,sub_district_code,sub_district_name,alternate_phone,customer_phone,phone,phone_number,additional_phone_number,owner_phone_number,owner_additional_phone_number,mobile_phone,full_name,legal_id_number"
     - name: HTTP_SERVER_RESPONSE_BODY_LOGGING
       value: "true"
@@ -127,5 +127,5 @@
       value: "32768"
     - name: HTTP_SERVER_RESPONSE_BODY_JSON_MASKED_FIELDS
-      value: ""
+      value: "access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_photo_id,idNumber,ktp,ktp_data,ktp_doc_id,ktp_number,mother_maiden_name,mother_name,new_password,new_password_confirmation,nik,npwp_number,old_password,otp,otp_token,password,placeOfBirth,pob,refresh_token,selfie,selfie_doc_id,selfie_photo_id,signature,token,religion,legal_address,birth_place,city_code,city_name,district_code,district_name,province_code,province_name,sub_district_code,sub_district_name,alternate_phone,customer_phone,phone,phone_number,additional_phone_number,owner_phone_number,owner_additional_phone_number,mobile_phone,full_name,legal_id_number"
     - name: HTTP_SERVER_BODY_LOGGING_ON_ERROR_ONLY
       value: "true"
@@ -154,5 +154,5 @@
       value: "32768"
     - name: HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS
-      value: ""
+      value: "access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_photo_id,idNumber,ktp,ktp_data,ktp_doc_id,ktp_number,mother_maiden_name,mother_name,new_password,new_password_confirmation,nik,npwp_number,old_password,otp,otp_token,password,placeOfBirth,pob,refresh_token,selfie,selfie_doc_id,selfie_photo_id,signature,token,religion,legal_address,birth_place,city_code,city_name,district_code,district_name,province_code,province_name,sub_district_code,sub_district_name,alternate_phone,customer_phone,phone,phone_number,additional_phone_number,owner_phone_number,owner_additional_phone_number,mobile_phone,full_name,legal_id_number"
     - name: HTTP_CLIENT_RESPONSE_BODY_LOGGING
       value: "true"
@@ -160,5 +160,5 @@
       value: "32768"
     - name: HTTP_CLIENT_RESPONSE_BODY_JSON_MASKED_FIELDS
-      value: ""
+      value: "access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_photo_id,idNumber,ktp,ktp_data,ktp_doc_id,ktp_number,mother_maiden_name,mother_name,new_password,new_password_confirmation,nik,npwp_number,old_password,otp,otp_token,password,placeOfBirth,pob,refresh_token,selfie,selfie_doc_id,selfie_photo_id,signature,token,religion,legal_address,birth_place,city_code,city_name,district_code,district_name,province_code,province_name,sub_district_code,sub_district_name,alternate_phone,customer_phone,phone,phone_number,additional_phone_number,owner_phone_number,owner_additional_phone_number,mobile_phone,full_name,legal_id_number"
     - name: HTTP_CLIENT_ENABLE_TRACING
       value: "true"
```

### `partnership-provisioning/values-prod.yaml`

- HTTP_SERVER_REQUEST_BODY_JSON_MASKED_FIELDS: '' -> 'access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_…
- HTTP_SERVER_RESPONSE_BODY_JSON_MASKED_FIELDS: '' -> 'access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity…
- HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS: '' -> 'access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_…
- HTTP_CLIENT_RESPONSE_BODY_JSON_MASKED_FIELDS: '' -> 'access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity…

```diff
--- a/partnership-provisioning/values-prod.yaml
+++ b/partnership-provisioning/values-prod.yaml
@@ -134,5 +134,5 @@
       value: "32768"
     - name: HTTP_SERVER_REQUEST_BODY_JSON_MASKED_FIELDS
-      value: ""
+      value: "access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_photo_id,idNumber,ktp,ktp_data,ktp_doc_id,ktp_number,mother_maiden_name,mother_name,new_password,new_password_confirmation,nik,npwp_number,old_password,otp,otp_token,password,placeOfBirth,pob,refresh_token,selfie,selfie_doc_id,selfie_photo_id,signature,token,religion,legal_address,birth_place,city_code,city_name,district_code,district_name,province_code,province_name,sub_district_code,sub_district_name,alternate_phone,customer_phone,phone,phone_number,additional_phone_number,owner_phone_number,owner_additional_phone_number,mobile_phone,full_name,legal_id_number"
     - name: HTTP_SERVER_RESPONSE_BODY_LOGGING
       value: "true"
@@ -140,5 +140,5 @@
       value: "32768"
     - name: HTTP_SERVER_RESPONSE_BODY_JSON_MASKED_FIELDS
-      value: ""
+      value: "access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_photo_id,idNumber,ktp,ktp_data,ktp_doc_id,ktp_number,mother_maiden_name,mother_name,new_password,new_password_confirmation,nik,npwp_number,old_password,otp,otp_token,password,placeOfBirth,pob,refresh_token,selfie,selfie_doc_id,selfie_photo_id,signature,token,religion,legal_address,birth_place,city_code,city_name,district_code,district_name,province_code,province_name,sub_district_code,sub_district_name,alternate_phone,customer_phone,phone,phone_number,additional_phone_number,owner_phone_number,owner_additional_phone_number,mobile_phone,full_name,legal_id_number"
     - name: HTTP_SERVER_BODY_LOGGING_ON_ERROR_ONLY
       value: "true"
@@ -159,5 +159,5 @@
       value: "32768"
     - name: HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS
-      value: ""
+      value: "access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_photo_id,idNumber,ktp,ktp_data,ktp_doc_id,ktp_number,mother_maiden_name,mother_name,new_password,new_password_confirmation,nik,npwp_number,old_password,otp,otp_token,password,placeOfBirth,pob,refresh_token,selfie,selfie_doc_id,selfie_photo_id,signature,token,religion,legal_address,birth_place,city_code,city_name,district_code,district_name,province_code,province_name,sub_district_code,sub_district_name,alternate_phone,customer_phone,phone,phone_number,additional_phone_number,owner_phone_number,owner_additional_phone_number,mobile_phone,full_name,legal_id_number"
     - name: HTTP_CLIENT_RESPONSE_BODY_LOGGING
       value: "true"
@@ -165,5 +165,5 @@
       value: "32768"
     - name: HTTP_CLIENT_RESPONSE_BODY_JSON_MASKED_FIELDS
-      value: ""
+      value: "access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_photo_id,idNumber,ktp,ktp_data,ktp_doc_id,ktp_number,mother_maiden_name,mother_name,new_password,new_password_confirmation,nik,npwp_number,old_password,otp,otp_token,password,placeOfBirth,pob,refresh_token,selfie,selfie_doc_id,selfie_photo_id,signature,token,religion,legal_address,birth_place,city_code,city_name,district_code,district_name,province_code,province_name,sub_district_code,sub_district_name,alternate_phone,customer_phone,phone,phone_number,additional_phone_number,owner_phone_number,owner_additional_phone_number,mobile_phone,full_name,legal_id_number"
     - name: HTTP_CLIENT_BODY_LOGGING_ON_ERROR_ONLY
       value: "false"
```

### `doc-renderer/values-prod.yaml`

- HTTP_SERVER_REQUEST_BODY_JSON_MASKED_FIELDS: '' -> 'access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_…
- HTTP_SERVER_RESPONSE_BODY_JSON_MASKED_FIELDS: '' -> 'access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity…
- HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS: '' -> 'access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_…
- HTTP_CLIENT_RESPONSE_BODY_JSON_MASKED_FIELDS: '' -> 'access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity…

```diff
--- a/doc-renderer/values-prod.yaml
+++ b/doc-renderer/values-prod.yaml
@@ -149,5 +149,5 @@
       value: "32768"
     - name: HTTP_SERVER_REQUEST_BODY_JSON_MASKED_FIELDS
-      value: ""
+      value: "access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_photo_id,idNumber,ktp,ktp_data,ktp_doc_id,ktp_number,mother_maiden_name,mother_name,new_password,new_password_confirmation,nik,npwp_number,old_password,otp,otp_token,password,placeOfBirth,pob,refresh_token,selfie,selfie_doc_id,selfie_photo_id,signature,token,religion,legal_address,birth_place,city_code,city_name,district_code,district_name,province_code,province_name,sub_district_code,sub_district_name,alternate_phone,customer_phone,phone,phone_number,additional_phone_number,owner_phone_number,owner_additional_phone_number,mobile_phone,full_name,legal_id_number"
     - name: HTTP_SERVER_RESPONSE_BODY_LOGGING
       value: "true"
@@ -155,5 +155,5 @@
       value: "32768"
     - name: HTTP_SERVER_RESPONSE_BODY_JSON_MASKED_FIELDS
-      value: ""
+      value: "access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_photo_id,idNumber,ktp,ktp_data,ktp_doc_id,ktp_number,mother_maiden_name,mother_name,new_password,new_password_confirmation,nik,npwp_number,old_password,otp,otp_token,password,placeOfBirth,pob,refresh_token,selfie,selfie_doc_id,selfie_photo_id,signature,token,religion,legal_address,birth_place,city_code,city_name,district_code,district_name,province_code,province_name,sub_district_code,sub_district_name,alternate_phone,customer_phone,phone,phone_number,additional_phone_number,owner_phone_number,owner_additional_phone_number,mobile_phone,full_name,legal_id_number"
     - name: HTTP_SERVER_BODY_LOGGING_ON_ERROR_ONLY
       value: "false"
@@ -173,5 +173,5 @@
       value: "32768"
     - name: HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS
-      value: ""
+      value: "access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_photo_id,idNumber,ktp,ktp_data,ktp_doc_id,ktp_number,mother_maiden_name,mother_name,new_password,new_password_confirmation,nik,npwp_number,old_password,otp,otp_token,password,placeOfBirth,pob,refresh_token,selfie,selfie_doc_id,selfie_photo_id,signature,token,religion,legal_address,birth_place,city_code,city_name,district_code,district_name,province_code,province_name,sub_district_code,sub_district_name,alternate_phone,customer_phone,phone,phone_number,additional_phone_number,owner_phone_number,owner_additional_phone_number,mobile_phone,full_name,legal_id_number"
     - name: HTTP_CLIENT_RESPONSE_BODY_LOGGING
       value: "true"
@@ -179,5 +179,5 @@
       value: "32768"
     - name: HTTP_CLIENT_RESPONSE_BODY_JSON_MASKED_FIELDS
-      value: ""
+      value: "access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_photo_id,idNumber,ktp,ktp_data,ktp_doc_id,ktp_number,mother_maiden_name,mother_name,new_password,new_password_confirmation,nik,npwp_number,old_password,otp,otp_token,password,placeOfBirth,pob,refresh_token,selfie,selfie_doc_id,selfie_photo_id,signature,token,religion,legal_address,birth_place,city_code,city_name,district_code,district_name,province_code,province_name,sub_district_code,sub_district_name,alternate_phone,customer_phone,phone,phone_number,additional_phone_number,owner_phone_number,owner_additional_phone_number,mobile_phone,full_name,legal_id_number"
     - name: HTTP_CLIENT_ENABLE_TRACING
       value: "true"
```

### `integrity/values-prod.yaml`

- GRPC_SERVER_REQUEST_BODY_JSON_MASKED_FIELDS: '' -> 'access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_…
- GRPC_SERVER_RESPONSE_BODY_JSON_MASKED_FIELDS: '' -> 'access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity…
- HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS: '' -> 'access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_…
- HTTP_CLIENT_RESPONSE_BODY_JSON_MASKED_FIELDS: '' -> 'access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity…

```diff
--- a/integrity/values-prod.yaml
+++ b/integrity/values-prod.yaml
@@ -166,5 +166,5 @@
       value: "32768"
     - name: GRPC_SERVER_REQUEST_BODY_JSON_MASKED_FIELDS
-      value: ""
+      value: "access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_photo_id,idNumber,ktp,ktp_data,ktp_doc_id,ktp_number,mother_maiden_name,mother_name,new_password,new_password_confirmation,nik,npwp_number,old_password,otp,otp_token,password,placeOfBirth,pob,refresh_token,selfie,selfie_doc_id,selfie_photo_id,signature,token,religion,legal_address,birth_place,city_code,city_name,district_code,district_name,province_code,province_name,sub_district_code,sub_district_name,alternate_phone,customer_phone,phone,phone_number,additional_phone_number,owner_phone_number,owner_additional_phone_number,mobile_phone,full_name,legal_id_number"
     - name: GRPC_SERVER_RESPONSE_BODY_LOGGING
       value: "true"
@@ -172,5 +172,5 @@
       value: "32768"
     - name: GRPC_SERVER_RESPONSE_BODY_JSON_MASKED_FIELDS
-      value: ""
+      value: "access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_photo_id,idNumber,ktp,ktp_data,ktp_doc_id,ktp_number,mother_maiden_name,mother_name,new_password,new_password_confirmation,nik,npwp_number,old_password,otp,otp_token,password,placeOfBirth,pob,refresh_token,selfie,selfie_doc_id,selfie_photo_id,signature,token,religion,legal_address,birth_place,city_code,city_name,district_code,district_name,province_code,province_name,sub_district_code,sub_district_name,alternate_phone,customer_phone,phone,phone_number,additional_phone_number,owner_phone_number,owner_additional_phone_number,mobile_phone,full_name,legal_id_number"
     - name: GRPC_SERVER_BODY_LOGGING_ON_ERROR_ONLY
       value: "false"
@@ -180,5 +180,5 @@
       value: "32768"
     - name: HTTP_CLIENT_REQUEST_BODY_JSON_MASKED_FIELDS
-      value: ""
+      value: "access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_photo_id,idNumber,ktp,ktp_data,ktp_doc_id,ktp_number,mother_maiden_name,mother_name,new_password,new_password_confirmation,nik,npwp_number,old_password,otp,otp_token,password,placeOfBirth,pob,refresh_token,selfie,selfie_doc_id,selfie_photo_id,signature,token,religion,legal_address,birth_place,city_code,city_name,district_code,district_name,province_code,province_name,sub_district_code,sub_district_name,alternate_phone,customer_phone,phone,phone_number,additional_phone_number,owner_phone_number,owner_additional_phone_number,mobile_phone,full_name,legal_id_number"
     - name: HTTP_CLIENT_RESPONSE_BODY_LOGGING
       value: "true"
@@ -186,5 +186,5 @@
       value: "32768"
     - name: HTTP_CLIENT_RESPONSE_BODY_JSON_MASKED_FIELDS
-      value: ""
+      value: "access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_photo_id,idNumber,ktp,ktp_data,ktp_doc_id,ktp_number,mother_maiden_name,mother_name,new_password,new_password_confirmation,nik,npwp_number,old_password,otp,otp_token,password,placeOfBirth,pob,refresh_token,selfie,selfie_doc_id,selfie_photo_id,signature,token,religion,legal_address,birth_place,city_code,city_name,district_code,district_name,province_code,province_name,sub_district_code,sub_district_name,alternate_phone,customer_phone,phone,phone_number,additional_phone_number,owner_phone_number,owner_additional_phone_number,mobile_phone,full_name,legal_id_number"
     - name: REDIS_HOST
       valueFrom:
```

### `pbf/values-prod.yaml`

- GRPC_SERVER_REQUEST_BODY_JSON_MASKED_FIELDS: '' -> 'access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_…
- GRPC_SERVER_RESPONSE_BODY_JSON_MASKED_FIELDS: '' -> 'access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity…

```diff
--- a/pbf/values-prod.yaml
+++ b/pbf/values-prod.yaml
@@ -282,5 +282,5 @@
       value: "32768"
     - name: GRPC_SERVER_REQUEST_BODY_JSON_MASKED_FIELDS
-      value: ""
+      value: "access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_photo_id,idNumber,ktp,ktp_data,ktp_doc_id,ktp_number,mother_maiden_name,mother_name,new_password,new_password_confirmation,nik,npwp_number,old_password,otp,otp_token,password,placeOfBirth,pob,refresh_token,selfie,selfie_doc_id,selfie_photo_id,signature,token,religion,legal_address,birth_place,city_code,city_name,district_code,district_name,province_code,province_name,sub_district_code,sub_district_name,alternate_phone,customer_phone,phone,phone_number,additional_phone_number,owner_phone_number,owner_additional_phone_number,mobile_phone,full_name,legal_id_number"
     - name: GRPC_SERVER_RESPONSE_BODY_LOGGING
       value: "true"
@@ -288,5 +288,5 @@
       value: "32768"
     - name: GRPC_SERVER_RESPONSE_BODY_JSON_MASKED_FIELDS
-      value: ""
+      value: "access_token,accessKey,account_number,address,address_detail,birth_date,dob,email,gender,identity_photo_id,idNumber,ktp,ktp_data,ktp_doc_id,ktp_number,mother_maiden_name,mother_name,new_password,new_password_confirmation,nik,npwp_number,old_password,otp,otp_token,password,placeOfBirth,pob,refresh_token,selfie,selfie_doc_id,selfie_photo_id,signature,token,religion,legal_address,birth_place,city_code,city_name,district_code,district_name,province_code,province_name,sub_district_code,sub_district_name,alternate_phone,customer_phone,phone,phone_number,additional_phone_number,owner_phone_number,owner_additional_phone_number,mobile_phone,full_name,legal_id_number"
     - name: GRPC_SERVER_BODY_LOGGING_ON_ERROR_ONLY
       value: "false"
```

## 3. Log bodies on failed calls only

### `doc-renderer/values-prod.yaml`

- HTTP_SERVER_BODY_LOGGING_ON_ERROR_ONLY: 'false' -> 'true'

```diff
--- a/doc-renderer/values-prod.yaml
+++ b/doc-renderer/values-prod.yaml
@@ -157,5 +157,5 @@
       value: ""
     - name: HTTP_SERVER_BODY_LOGGING_ON_ERROR_ONLY
-      value: "false"
+      value: "true"
     - name: HTTP_CLIENT_DIAL_TIMEOUT
       value: "900"
```

### `portfolio-management-service/values-prod.yaml`

- HTTP_SERVER_BODY_LOGGING_ON_ERROR_ONLY: 'false' -> 'true'

```diff
--- a/portfolio-management-service/values-prod.yaml
+++ b/portfolio-management-service/values-prod.yaml
@@ -126,5 +126,5 @@
       value: "ktp_number,phone_number,account_number,mothers_maiden_name"
     - name: HTTP_SERVER_BODY_LOGGING_ON_ERROR_ONLY
-      value: "false"
+      value: "true"
     - name: OPENAPI_UI_ENABLE
       value: "true"
```

### `database-catalog/values-prod.yaml`

- HTTP_SERVER_BODY_LOGGING_ON_ERROR_ONLY: 'false' -> 'true'

```diff
--- a/database-catalog/values-prod.yaml
+++ b/database-catalog/values-prod.yaml
@@ -96,5 +96,5 @@
       value: ""
     - name: HTTP_SERVER_BODY_LOGGING_ON_ERROR_ONLY
-      value: "false"
+      value: "true"
 
     - name: HTTP_SERVER_BASE_PATH
```

## 4. bravo-onboarding-service stops logging request bodies

### `onboarding/values-prod.yaml`

Add next to the existing `RESPONSE_BODY_LOGGING: "false"` (line 1159):

```yaml
    - name: REQUEST_BODY_LOGGING
      value: "false"
```

