import re

class CNPJValidator:
    @staticmethod
    def clean_cnpj(cnpj: str) -> str:
        """Normaliza CNPJ: remove formatação (./-) e retorna apenas dígitos"""
        if not cnpj:
            return ''
        return re.sub(r'\D', '', str(cnpj))
    
    @staticmethod
    def validate_cnpj_format(cnpj: str) -> bool:
        """Valida se CNPJ tem exatamente 14 dígitos (após limpar formatação)"""
        cnpj_clean = CNPJValidator.clean_cnpj(cnpj)
        return len(cnpj_clean) == 14
    
    @staticmethod
    def validate_cnpj(cnpj: str) -> bool:
        cnpj = CNPJValidator.clean_cnpj(cnpj)
        
        if len(cnpj) != 14:
            return False
        
        if cnpj == cnpj[0] * 14:
            return False
        
        def calculate_digit(cnpj_partial: str, weights: list) -> int:
            total = sum(int(digit) * weight for digit, weight in zip(cnpj_partial, weights))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        weights_first = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        weights_second = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        
        first_digit = calculate_digit(cnpj[:12], weights_first)
        if first_digit != int(cnpj[12]):
            return False
        
        second_digit = calculate_digit(cnpj[:13], weights_second)
        if second_digit != int(cnpj[13]):
            return False
        
        return True
    
    @staticmethod
    def try_fix_cnpj(cnpj: str) -> tuple[str, bool]:
        """Tenta normalizar CNPJ: apenas aceita se tiver 14 dígitos exatos"""
        cnpj_clean = CNPJValidator.clean_cnpj(cnpj)
        
        # Aceita APENAS se tiver exatamente 14 dígitos
        if len(cnpj_clean) == 14 and CNPJValidator.validate_cnpj(cnpj_clean):
            return cnpj_clean, True
        
        # Caso contrário, invalida
        return cnpj_clean, False

class DataValidator:
    def __init__(self):
        self.validation_log = []
    
    def validate_dataframe(self, df):
        import pandas as pd
        
        print("Validando dados...")
        
        df['CNPJ_Original'] = df['CNPJ']
        df['CNPJ'] = df['CNPJ'].apply(CNPJValidator.clean_cnpj)
        
        invalid_cnpjs = []
        fixed_cnpjs = []
        
        for idx, row in df.iterrows():
            cnpj = row['CNPJ']
            
            if not CNPJValidator.validate_cnpj(cnpj):
                fixed_cnpj, is_valid = CNPJValidator.try_fix_cnpj(cnpj)
                
                if is_valid:
                    df.at[idx, 'CNPJ'] = fixed_cnpj
                    fixed_cnpjs.append({
                        'original': row['CNPJ_Original'],
                        'corrigido': fixed_cnpj
                    })
                else:
                    invalid_cnpjs.append({
                        'cnpj': row['CNPJ_Original'],
                        'razao_social': row.get('RazaoSocial', ''),
                        'motivo': 'Dígitos verificadores inválidos'
                    })
        
        print(f"CNPJs corrigidos: {len(fixed_cnpjs)}")
        print(f"CNPJs inválidos encontrados: {len(invalid_cnpjs)}")
        
        df = df[df['CNPJ'].apply(CNPJValidator.validate_cnpj)]
        
        original_count = len(df)
        df = df[df['ValorDespesas'] > 0]
        removed_count = original_count - len(df)
        if removed_count > 0:
            print(f"Removidos {removed_count} registros com valores não positivos")
        
        original_count = len(df)
        df = df[df['RazaoSocial'].notna() & (df['RazaoSocial'].str.strip() != '')]
        removed_count = original_count - len(df)
        if removed_count > 0:
            print(f"Removidos {removed_count} registros com razão social vazia")
        
        self.validation_log = {
            'invalid_cnpjs': invalid_cnpjs,
            'fixed_cnpjs': fixed_cnpjs,
            'total_validated': len(df)
        }
        
        print(f"Registros válidos: {len(df)}")
        
        return df
    
    def save_validation_log(self, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("LOG DE VALIDAÇÃO\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Total de registros validados: {self.validation_log['total_validated']}\n\n")
            
            f.write(f"CNPJs corrigidos: {len(self.validation_log['fixed_cnpjs'])}\n")
            for entry in self.validation_log['fixed_cnpjs'][:20]:
                f.write(f"  {entry['original']} -> {entry['corrigido']}\n")
            if len(self.validation_log['fixed_cnpjs']) > 20:
                f.write(f"  ... e mais {len(self.validation_log['fixed_cnpjs']) - 20}\n")
            
            f.write(f"\nCNPJs inválidos (removidos): {len(self.validation_log['invalid_cnpjs'])}\n")
            for entry in self.validation_log['invalid_cnpjs'][:20]:
                f.write(f"  {entry['cnpj']} - {entry['razao_social']} - {entry['motivo']}\n")
            if len(self.validation_log['invalid_cnpjs']) > 20:
                f.write(f"  ... e mais {len(self.validation_log['invalid_cnpjs']) - 20}\n")
        
        print(f"Log de validação salvo: {output_path}")
