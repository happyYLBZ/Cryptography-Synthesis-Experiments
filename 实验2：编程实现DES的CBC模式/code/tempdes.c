#include <openssl/des.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <inttypes.h>

#define ENC 1
#define DEC 0
#define CHUNK_SIZE 16

//检测字符是否是十六进制数字
int isAlnum(char c) {
    return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') ;
}

int main(int argc,char *argv[])
{
    int iv_length = strlen(argv[1]);
    int key_length = strlen(argv[2]);
    //检测初始向量和密钥的长度
    if(iv_length!=16){
	printf("Length of iv is not valid! \n");
	return 1;
    }
    if(key_length!=16){
	printf("Length of key is not valid! \n");
	return 1;
    }
    //检测初始向量和密钥的字符
    {
    
    char* iv = argv[1];
    int i = 0;
    while (++i<=16) {
        if (!isAlnum(*iv)) {
            printf("The characters of iv are not valid! \n");
            return 1; // 如果不是字母或数字，返回1
        }
        iv++;
    }
    i=0;
    char* key = argv[2];
    while (++i<=16) {
        if (!isAlnum(*key)) {
            printf("The characters of key are not valid! \n");
            return 1; // 如果不是字母或数字，返回1
        }
        key++;
    }

    }
    
    // 定义DES密钥和密钥调度表
    DES_cblock key;
    DES_key_schedule schedule;
    // 将字符串形式的密钥转换为DES_cblock类型的密钥
    memcpy(&key, argv[2], 8);
    // 使用DES_set_key_unchecked函数设置密钥
    DES_set_key_unchecked(&key, &schedule);
    
    
    int operation = 0;
    //输入文件  
    FILE *input = fopen(argv[3], "rb");
    if(input==NULL){
        perror("Error opening file \n");
        return 1;
    }
    //输出文件
    FILE *output = fopen(argv[4],"w");
    if(output==NULL){
        perror("Error opening file \n");
        return 1;
    }
    
    //将文件内容转化为16进制格式
    {
    
    FILE *hex_file;
    char buffer[16]; // 缓冲区大小，每次最多读取16个字节
    size_t bytes_read;
    hex_file = fopen("hex_output.txt", "w"); // 以文本写入方式打开文件

    // 检查输出文件是否成功打开
    if (hex_file == NULL) {
        printf("无法创建文件 %s\n", "hex_output.txt");
        return 1;
    }
    // 逐块读取文件内容并以十六进制格式写入输出文件
    while ((bytes_read = fread(buffer, 1, sizeof(buffer), input)) > 0) {
        for (size_t i = 0; i < bytes_read; ++i) {
            fprintf(hex_file, "%02X", buffer[i]); // 以十六进制格式写入每个字节的内容
        }
    }
    // 关闭文件
    fclose(hex_file);
    
    }
    
    FILE *hex_file;
    hex_file = fopen("hex_output.txt", "rb");
    
    // 使用strtoull函数将十六进制字符串转换为uint64_t类型
    uint64_t iv_64 = strtoull(argv[1], NULL, 16);
    
    // 缓冲区
    char buffer[CHUNK_SIZE + 1];
    char temp[CHUNK_SIZE + 1];
    uint64_t temp_64;
    uint32_t temp_32[2];
    uint64_t Ciphertext_block ; //密文
    uint64_t Plaintext_block ; //明文
    char last_block[CHUNK_SIZE + 1];
    bool first = true;
    
    
    //加密
    if (strcmp(argv[5], "encrypt") == 0) {
    
           operation = ENC;
	    // 每次读取十六个字符
	    while (fgets(buffer, sizeof(buffer), hex_file)){
	        
	            //不满16则用0补齐
		    if(strlen(buffer)<16){
		       for(int i=strlen(buffer);i<16;i++){
			buffer[i]='0';
		       }
			    buffer[16]='\0';
			    Plaintext_block = strtoull(buffer,NULL,16);//明文
			    temp_64 = Plaintext_block^Ciphertext_block;
			    //转化为uint32_t类型
			    temp_32[0] = (uint32_t)(temp_64 >> 32); //取高32位
			    temp_32[1] = (uint32_t)(temp_64  & 0xFFFFFFFF); //取低32位
			    //DES加密
			    DES_encrypt1(temp_32,&schedule,operation);
			    Ciphertext_block = ((uint64_t)temp_32[0] << 32) | (uint64_t)temp_32[1]; 
			    fprintf(output,"%016" PRIx64,Ciphertext_block);
			    break;
		    
		    }
		    
		if(first){
		    first = false;
		    Plaintext_block = strtoull(buffer,NULL,16); //明文
		    temp_64 = Plaintext_block^iv_64;
		    //转化为uint32_t类型
		    temp_32[0] = (uint32_t)(temp_64 >> 32); //取高32位
		    temp_32[1] = (uint32_t)(temp_64  & 0xFFFFFFFF); //取低32位
		    //DES加密
		    DES_encrypt1(temp_32,&schedule,operation);
		    Ciphertext_block = ((uint64_t)temp_32[0] << 32) | (uint64_t)temp_32[1]; 
		    fprintf(output,"%016" PRIx64,Ciphertext_block);
		}  
		else{
		    Plaintext_block = strtoull(buffer,NULL,16); //明文
		    temp_64 = Plaintext_block^Ciphertext_block;
		    //转化为uint32_t类型
		    temp_32[0] = (uint32_t)(temp_64 >> 32); //取高32位
		    temp_32[1] = (uint32_t)(temp_64  & 0xFFFFFFFF); //取低32位
		    //DES加密
		    DES_encrypt1(temp_32,&schedule,operation);
		    Ciphertext_block = ((uint64_t)temp_32[0] << 32) | (uint64_t)temp_32[1]; 
		    fprintf(output,"%016" PRIx64,Ciphertext_block);
		}
	    }
       
    
    }
    //解密
    uint64_t last;
    if (strcmp(argv[5], "decrypt") == 0) {

	    operation = DEC;
	    // 每次读取十六个字符
	    while (fgets(buffer, sizeof(buffer), hex_file)){
	    //不满16则用0补齐
	    if(strlen(buffer)<16){
	       for(int i=strlen(buffer);i<16;i++){
		buffer[i]='0';
	       }
		    buffer[16]='\0';
		    Ciphertext_block = strtoull(buffer,NULL,16);//密文
		    //转化为uint32_t类型
		    temp_32[0] = (uint32_t)(Ciphertext_block >> 32); //取高32位
		    temp_32[1] = (uint32_t)(Ciphertext_block  & 0xFFFFFFFF); //取低32位
		    //DES解密
		    DES_encrypt1(temp_32,&schedule,operation);
		    temp_64 = ((uint64_t)temp_32[0] << 32) | (uint64_t)temp_32[1]; 
		    Plaintext_block = temp_64^last;
		    fprintf(output,"%016" PRIx64,Plaintext_block);
		    break;
	    }

		if(first){
		    first = false;
		    Ciphertext_block = strtoull(buffer,NULL,16);//密文
		    
		    //转化为uint32_t类型
		    temp_32[0] = (uint32_t)(Ciphertext_block >> 32); //取高32位
		    temp_32[1] = (uint32_t)(Ciphertext_block  & 0xFFFFFFFF); //取低32位
		    //DES解密
		    DES_encrypt1(temp_32,&schedule,operation);
		    temp_64 = ((uint64_t)temp_32[0] << 32) | (uint64_t)temp_32[1]; 
		    Plaintext_block = temp_64^iv_64; 
		    fprintf(output,"%016" PRIx64,Plaintext_block);
		    last = Ciphertext_block;
		}  
		else{

		    Ciphertext_block = strtoull(buffer,NULL,16);//密文  
		    //转化为uint32_t类型
		    temp_32[0] = (uint32_t)(Ciphertext_block >> 32); //取高32位
		    temp_32[1] = (uint32_t)(Ciphertext_block  & 0xFFFFFFFF); //取低32位
		    //DES解密
		    DES_encrypt1(temp_32,&schedule,operation);
		    temp_64 = ((uint64_t)temp_32[0] << 32) | (uint64_t)temp_32[1]; 
		    Plaintext_block = temp_64^last;
		    fprintf(output,"%016" PRIx64,Plaintext_block);
		    last = Ciphertext_block;
		}
	    }

    }
    
    // 关闭文件
    fclose(input);
    // 关闭文件
    fclose(output);
    fclose(hex_file);

    return 0;
    
}


