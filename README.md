
# KYC Solution SpandsSPS API

KYC (Know Your Customer) API built with FastAPI, OpenCV, and ONNX models for facial recognition and validation. This solution allows you to verify the identity of a person by comparing their passport photo and profile image, checking the validity of each image, and extracting passport details if a face is detected.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [API Endpoints](#api-endpoints)
  - [Client Examples](#client-examples)
- [Running the Server](#running-the-server)
- [Dependencies](#dependencies)

---

## Features

- **Face Detection:** Identifies if there is a valid face in passport and profile images.
- **Face Comparison:** Compares faces in passport and profile images for identity verification.
- **Passport Info Extraction:** Extracts information from the passport and returns a cropped face image if available.

---

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/KYC-Solution-SpandsSPS.git
   cd KYC-Solution-SpandsSPS
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Ensure that the necessary AI model files are available in the `ai_models` directory:
   - `face_recognition_sface_2021dec.onnx`
   - `face_detection_yunet_2023mar.onnx`

4. Start the FastAPI server:

   ```bash
   uvicorn app:app --host 127.0.0.1 --port 8000
   ```

---

## Usage

### API Endpoints

1. **Client Example Code**

   - **Endpoint:** `GET /`
   - **Description:** Code Example for different clietns.
   - **Response:**
     HTML Web Page

2. **Validate Passport Face**

   - **Endpoint:** `POST /is_passport_valid`
   - **Parameters:** `passport_file` (file, required)
   - **Response:**
     ```json
     {
       "is_passport_has_valid_face": true | false
     }
     ```

3. **Validate Profile Face**

   - **Endpoint:** `POST /is_profile_valid`
   - **Parameters:** `profile_file` (file, required)
   - **Response:**
     ```json
     {
       "is_profile_has_valid_face": true | false
     }
     ```

4. **Verify Faces in Passport and Profile**

   - **Endpoint:** `POST /verify_both_faces`
   - **Parameters:** `passport_file` and `profile_file` (both files, required)
   - **Response:**
     ```json
     {
       "is_passport_has_valid_face": true | false,
       "is_profile_has_valid_face": true | false,
       "matched": true | false
     }
     ```

5. **Read Passport Information**

   - **Endpoint:** `POST /read_passport_info`
   - **Parameters:** `passport_file` (file, required)
   - **Response:**
     ```json
     {
       "passport_info": {
         "is_face": true | false,
         "base64_face": "data:image/jpeg;base64,<Base64EncodedImage>"
       }
     }
     ```

---

### Client Examples

#### ReactJS

```javascript
import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [passport, setPassport] = useState(null);
  const [profile, setProfile] = useState(null);
  const [result, setResult] = useState(null);

  const handlePassportChange = (e) => setPassport(e.target.files[0]);
  const handleProfileChange = (e) => setProfile(e.target.files[0]);

  const verifyFaces = async () => {
    const formData = new FormData();
    formData.append('passport_file', passport);
    formData.append('profile_file', profile);

    try {
      const response = await axios.post('http://127.0.0.1:8000/verify_both_faces', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div>
      <h1>KYC Solution Verification</h1>
      <input type="file" onChange={handlePassportChange} />
      <input type="file" onChange={handleProfileChange} />
      <button onClick={verifyFaces}>Verify</button>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}

export default App;
```

#### Node.js

```javascript
const axios = require('axios');
const fs = require('fs');

async function verifyFaces() {
  const formData = new FormData();
  formData.append('passport_file', fs.createReadStream('path/to/passport.jpg'));
  formData.append('profile_file', fs.createReadStream('path/to/profile.jpg'));

  try {
    const response = await axios.post('http://127.0.0.1:8000/verify_both_faces', formData, {
      headers: formData.getHeaders()
    });
    console.log('Verification Result:', response.data);
  } catch (error) {
    console.error('Error verifying faces:', error);
  }
}

verifyFaces();
```

#### TypeScript

```typescript
import axios, { AxiosResponse } from 'axios';

async function verifyFaces(passportFile: File, profileFile: File): Promise<void> {
  const formData = new FormData();
  formData.append('passport_file', passportFile);
  formData.append('profile_file', profileFile);

  try {
    const response: AxiosResponse = await axios.post('http://127.0.0.1:8000/verify_both_faces', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    console.log('Verification Result:', response.data);
  } catch (error) {
    console.error('Error verifying faces:', error);
  }
}
```

#### React Native

```javascript
import React, { useState } from 'react';
import { View, Button, Text } from 'react-native';
import axios from 'axios';
import * as ImagePicker from 'react-native-image-picker';

export default function App() {
  const [result, setResult] = useState(null);

  const pickImage = async (setter) => {
    ImagePicker.launchImageLibrary({}, (response) => {
      if (response.assets) {
        setter(response.assets[0].uri);
      }
    });
  };

  const verifyFaces = async (passportUri, profileUri) => {
    const formData = new FormData();
    formData.append('passport_file', {
      uri: passportUri,
      name: 'passport.jpg',
      type: 'image/jpeg',
    });
    formData.append('profile_file', {
      uri: profileUri,
      name: 'profile.jpg',
      type: 'image/jpeg',
    });

    try {
      const response = await axios.post('http://127.0.0.1:8000/verify_both_faces', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <View>
      <Button title="Pick Passport Image" onPress={() => pickImage(setPassport)} />
      <Button title="Pick Profile Image" onPress={() => pickImage(setProfile)} />
      <Button title="Verify Faces" onPress={() => verifyFaces(passport, profile)} />
      {result && <Text>{JSON.stringify(result, null, 2)}</Text>}
    </View>
  );
}
```

---

## Running the Server

To start the server, run:

```bash
uvicorn app:app --host 127.0.0.1 --port 8000
```

## Dependencies

- `FastAPI`
- `uvicorn`
- `opencv-python`
- `numpy`
- `base64`

---
