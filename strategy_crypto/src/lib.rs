use aes_gcm::aead::{Aead, KeyInit};
use aes_gcm::{Aes256Gcm, Nonce}; // 96-bit nonce
use base64::{engine::general_purpose::STANDARD, Engine};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use rand::rngs::OsRng;
use rand::RngCore;

// 默认内置密钥（32 字节）。仅供无环境变量场景使用，生产请覆盖。
const DEFAULT_KEY: &str = "agfdsfsdafsdafdsafsdafdsafdfghdy";

/// 将 hex/base64/原始 32 字节 key 字符串解析为 32 字节 key
fn parse_key(key_str: &str) -> PyResult<[u8; 32]> {
    let key_input = if key_str.is_empty() {
        DEFAULT_KEY
    } else {
        key_str
    };

    if key_input.len() == 32 {
        // 视为原始 utf-8 长度 32；不推荐但兼容
        let bytes = key_input.as_bytes();
        if bytes.len() == 32 {
            let mut k = [0u8; 32];
            k.copy_from_slice(bytes);
            return Ok(k);
        }
    }
    if let Ok(raw) = hex::decode(key_input) {
        if raw.len() == 32 {
            let mut k = [0u8; 32];
            k.copy_from_slice(&raw);
            return Ok(k);
        }
    }
    if let Ok(raw) = STANDARD.decode(key_input) {
        if raw.len() == 32 {
            let mut k = [0u8; 32];
            k.copy_from_slice(&raw);
            return Ok(k);
        }
    }
    Err(PyValueError::new_err(
        "STRATEGY_KEY 需为 32 字节 hex/base64/原始字符串",
    ))
}

/// 输出格式：nonce(12 bytes) + ciphertext||tag
#[pyfunction]
fn encrypt_bytes(py: Python<'_>, key: &str, plaintext: &[u8]) -> PyResult<Py<PyBytes>> {
    let key_bytes = parse_key(key)?;
    let cipher =
        Aes256Gcm::new_from_slice(&key_bytes).map_err(|e| PyValueError::new_err(e.to_string()))?;
    let mut nonce_bytes = [0u8; 12];
    OsRng.fill_bytes(&mut nonce_bytes);
    let nonce = Nonce::from_slice(&nonce_bytes);
    let mut out = nonce_bytes.to_vec();
    let ct = cipher
        .encrypt(nonce, plaintext)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    out.extend_from_slice(&ct);
    Ok(PyBytes::new(py, &out).into())
}

#[pyfunction]
fn decrypt_bytes(py: Python<'_>, key: &str, blob: &[u8]) -> PyResult<Py<PyBytes>> {
    if blob.len() < 12 {
        return Err(PyValueError::new_err("密文格式错误，长度不足"));
    }
    let key_bytes = parse_key(key)?;
    let cipher =
        Aes256Gcm::new_from_slice(&key_bytes).map_err(|e| PyValueError::new_err(e.to_string()))?;
    let (nonce_bytes, ct) = blob.split_at(12);
    let nonce = Nonce::from_slice(nonce_bytes);
    let pt = cipher
        .decrypt(nonce, ct)
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
    Ok(PyBytes::new(py, &pt).into())
}

#[pymodule]
fn strategy_crypto(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(encrypt_bytes, m)?)?;
    m.add_function(wrap_pyfunction!(decrypt_bytes, m)?)?;
    Ok(())
}
