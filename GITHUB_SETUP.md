# Instruções para Publicar no GitHub

Siga estes passos para publicar o projeto no GitHub:

## 1. Inicializar Repositório Git

```bash
cd /Users/leandrobosaipo/Sites/scripts/arkhe-video
git init
```

## 2. Adicionar Arquivos

```bash
git add .
```

## 3. Criar Commit Inicial

```bash
git commit -m "Initial commit: Arkhe Video API with Swagger documentation"
```

## 4. Renomear Branch para main

```bash
git branch -M main
```

## 5. Adicionar Remote do GitHub

```bash
git remote add origin https://github.com/leandrobosaipo/arkhe-video.git
```

## 6. Verificar Remote

```bash
git remote -v
```

Deve mostrar:
```
origin  https://github.com/leandrobosaipo/arkhe-video.git (fetch)
origin  https://github.com/leandrobosaipo/arkhe-video.git (push)
```

## 7. Fazer Push para GitHub

```bash
git push -u origin main
```

## Comandos Completos (Copy-Paste)

```bash
cd /Users/leandrobosaipo/Sites/scripts/arkhe-video
git init
git add .
git commit -m "Initial commit: Arkhe Video API with Swagger documentation"
git branch -M main
git remote add origin https://github.com/leandrobosaipo/arkhe-video.git
git push -u origin main
```

## Verificação

Após o push, verifique no GitHub:
- Todos os arquivos foram enviados
- O README.md está visível
- Os arquivos de documentação estão presentes

## Próximos Passos

Após publicar no GitHub:
1. Configure o deploy no EasyPanel usando o repositório
2. Configure as variáveis de ambiente no EasyPanel
3. Teste a API após o deploy

## Notas Importantes

- Certifique-se de que arquivos sensíveis (`.env`, credenciais) não foram commitados
- O arquivo `.gitignore` já está configurado para ignorar arquivos sensíveis
- Nunca commite credenciais ou chaves de API

